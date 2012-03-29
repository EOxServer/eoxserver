#include <stdio.h>
#include <string.h>

#include <gdal/gdal.h>
#include <gdal/gdal_alg.h>
#include <gdal/gdalwarper.h>
#include <gdal/ogr_srs_api.h>

typedef struct {
    size_t n_points;
    double *x;
    double *y;
} eoxs_footprint;

typedef struct {
    int srid;
    double minx;
    double miny;
    double maxx;
    double maxy;
} eoxs_subset;

typedef struct {
    int x_off;
    int y_off;
    int x_size;
    int y_size;
} eoxs_rect;

void eoxs_destroy_footprint(eoxs_footprint *fp) {
    free(fp->x);
    free(fp->y);
    free(fp);
}

void eoxs_free_string(char* str)
{
    free(str);
}

void *eoxs_get_referenceable_grid_transformer(GDALDatasetH ds) {
    int gcp_count;
    const GDAL_GCP *gcps;
    
    if (!ds) return NULL;
    
    gcp_count = GDALGetGCPCount(ds);
    gcps = GDALGetGCPs(ds);
    
    return GDALCreateGCPTransformer(gcp_count, gcps, 1, FALSE);
}

void eoxs_destroy_referenceable_grid_transformer(void *transformer) {
    GDALDestroyGCPTransformer(transformer);
}

eoxs_footprint *eoxs_calculate_footprint(GDALDatasetH ds) {
    void *transformer;
    int x_size, y_size;
    double *x, *y, *z;

    int x_e, y_e;
    size_t n_points;
    int *success;
    int i;

    eoxs_footprint *ret;

    if (!ds) {
        fprintf(stderr, "Error processing dataset.");
        return NULL;
    }

    x_size = GDALGetRasterXSize(ds);
    y_size = GDALGetRasterYSize(ds);

    transformer = eoxs_get_referenceable_grid_transformer(ds);

    if (!transformer)
    {
        fprintf(stderr, "Could not create GCP transformer.");
        return NULL;
    }

    x_e = x_size / 100 - 1; if (x_e < 0) x_e = 0;
    y_e = y_size / 100 - 1; if (y_e < 0) y_e = 0;
    n_points = 4 + 2 * x_e + 2 * y_e;

    x = malloc(sizeof(double) * n_points);
    y = malloc(sizeof(double) * n_points);
    z = malloc(sizeof(double) * n_points);
    success = malloc(sizeof(int) * n_points);

    x[0] = 0; y[0] = 0; z[0] = 0;
    for (i=1; i <= x_e; i++) {
        x[i] = (double) i * x_size / x_e;
        y[i] = 0;
        z[i] = 0;
    }
    x[x_e+1] = (double) x_size; y[x_e+1] = 0; z[x_e+1] = 0;
    for (i=1; i<=y_e; i++) {
        x[x_e+1+i] = (double) x_size;
        y[x_e+1+i] = (double) i * y_size / y_e;
        z[x_e+1+i] = 0;
    }
    x[x_e+1+y_e+1] = (double) x_size; y[x_e+1+y_e+1] = (double) y_size; z[x_e+1+y_e+1] = 0;
    for (i=1; i<=x_e; i++) {
        x[x_e+1+y_e+1+i] = (double) x_size - i * x_size / x_e;
        y[x_e+1+y_e+1+i] = (double) y_size;
        z[x_e+1+y_e+1+i] = 0;
    }
    x[x_e+1+y_e+1+x_e+1] = 0; y[x_e+1+y_e+1+x_e+1] = (double) y_size; z[x_e+1+y_e+1+x_e+1] = 0;
    for (i=1; i<=y_e; i++) {
        x[x_e+1+y_e+1+x_e+1+i] = 0;
        y[x_e+1+y_e+1+x_e+1+i] = (double) y_size - i * y_size / y_e;
        z[x_e+1+y_e+1+x_e+1+i] = 0;
    }

    GDALGCPTransform(transformer, FALSE, n_points, x, y, z, success);

    // discard unused information
    free(z);
    free(success);
    eoxs_destroy_referenceable_grid_transformer(transformer);

    ret = malloc(sizeof(eoxs_footprint));
    ret->n_points = n_points;
    ret->x = x;
    ret->y = y;

    return ret;
}

const char *eoxs_get_footprint_wkt(GDALDatasetH ds) {
    eoxs_footprint *fp;
    char *wkt, buffer[256];
    int i;
    fp = eoxs_calculate_footprint(ds);

    if (!fp) return NULL;

    wkt = calloc((fp->n_points + 1) * 100 + sizeof("POLYGON(())"), sizeof(char));
    sprintf(wkt, "POLYGON((");

    for (i=0; i<fp->n_points; ++i) {
        sprintf(buffer, "%f %f", fp->x[i], fp->y[i]);
        if(i != 0) {
            strcat(wkt, ",");
        }
        strcat(wkt, buffer);
    }

    sprintf(buffer, ",%f %f", fp->x[0], fp->y[0]);
    strcat(wkt, buffer);
    strcat(wkt, "))");

    // clean up
    eoxs_destroy_footprint(fp);

    return wkt;
}

double eoxs_array_min(int n, double *c) {
    double min_value;
    int i;
    
    min_value = c[0];
    
    for (i=1; i<n; i++) {
        if (c[i] < min_value) min_value = c[i];
    }
    
    return min_value;
}

double eoxs_array_max(int n, double *c) {
    double max_value;
    int i;
    
    max_value = c[0];
    
    for (i=1; i<n; i++) {
        if (c[i] > max_value) max_value = c[i];
    }

    return max_value;
}

void eoxs_get_intermediate_point_count(
    int *n_x,
    int *n_y,
    int ds_x_size,
    int ds_y_size,
    eoxs_subset *subset,
    void *transformer,
    OGRCoordinateTransformationH ct
) {
    double x[4], y[4], z[4];
    int success[4];
    
    double dist;
    
    x[0] = 0; y[0] = 0; z[0] = 0;
    x[1] = (double) ds_x_size; y[1] = 0; z[1] = 0;
    x[2] = (double) ds_x_size; y[2] = (double) ds_y_size; z[2] = 0;
    x[3] = 0; y[3] = (double) ds_y_size; z[3] = 0;
    
    GDALGCPTransform(transformer, FALSE, 4, x, y, z, success);
    
    dist = MIN(
        (eoxs_array_max(4, x) - eoxs_array_min(4, x)) / (double) (ds_x_size / 100),
        (eoxs_array_max(4, y) - eoxs_array_min(4, y)) / (double) (ds_y_size / 100)
    );
    
    x[0] = subset->minx; y[0] = subset->miny; z[0] = 0;
    x[1] = subset->maxx; y[1] = subset->miny; z[1] = 0;
    x[2] = subset->maxx; y[2] = subset->maxy; z[2] = 0;
    x[3] = subset->minx; y[3] = subset->maxy; z[3] = 0;
    
    OCTTransform(ct, 4, x, y, z);
    
    *n_x = (int) ceil((eoxs_array_max(4, x) - eoxs_array_min(4, x)) / dist);
    *n_y = (int) ceil((eoxs_array_max(4, y) - eoxs_array_min(4, y)) / dist);
}

int eoxs_rect_from_subset(GDALDatasetH ds, eoxs_subset *subset, eoxs_rect *out_rect) {
    void *transformer;
    
    const char *tmp;
    char *gcp_proj_wkt;
    
    OGRSpatialReferenceH gcp_srs, subset_srs;
    OGRCoordinateTransformationH ct;
    
    int ds_x_size, ds_y_size;
    int n_points, n_x, n_y;
    
    double *x, *y, *z;
    int *success;
    
    double x_step, y_step;
    int b;
    
    int minx, miny, maxx, maxy;
    int i;
    
    if (!ds) return 0;
    
    ds_x_size = GDALGetRasterXSize(ds);
    ds_y_size = GDALGetRasterYSize(ds);
    
    tmp = GDALGetGCPProjection(ds);
    gcp_proj_wkt = malloc(strlen(tmp));
    strcpy(gcp_proj_wkt, tmp);
    
    transformer = eoxs_get_referenceable_grid_transformer(ds);
    
    if (!transformer) {
        free(gcp_proj_wkt);
        return 0;
    }
    
    gcp_srs = OSRNewSpatialReference(gcp_proj_wkt);
    subset_srs = OSRNewSpatialReference("");
    OSRImportFromEPSG(subset_srs, subset->srid);
    
    ct = OCTNewCoordinateTransformation(subset_srs, gcp_srs);
    if (!ct) {
        free(gcp_proj_wkt);
        eoxs_destroy_referenceable_grid_transformer(transformer);
        return 0;
    }
    
    eoxs_get_intermediate_point_count(&n_x, &n_y, ds_x_size, ds_y_size, subset, transformer, ct);
    
    n_points = 4 + 2*n_x + 2*n_y;
    
    x = malloc(n_points * sizeof(double));
    y = malloc(n_points * sizeof(double));
    z = malloc(n_points * sizeof(double));
    success = malloc(n_points * sizeof(int));
    
    x_step = (subset->maxx - subset->minx) / (double) n_x;
    y_step = (subset->maxy - subset->miny) / (double) n_y;
    
    x[0] = subset->minx; y[0] = subset->miny; z[0] = 0;
    for (i=1; i<=n_x; i++) {
        x[i] = subset->minx + (double) i * x_step;
        y[i] = subset->miny;
        z[i] = 0;
    }
    b = n_x+1;
    x[b] = subset->maxx; y[b] = subset->miny; z[b] = 0;
    for (i=1; i<=n_y; i++) {
        x[b+i] = subset->maxx;
        y[b+i] = subset->miny + (double) i * y_step;
        z[b+i] = 0;
    }
    b = n_x+1+n_y+1;
    x[b] = subset->maxx; y[b] = subset->maxy; z[b] = 0;
    for (i=1; i<=n_x; i++) {
        x[b+i] = subset->maxx - (double) i * x_step;
        y[b+i] = subset->maxy;
        z[b+i] = 0;
    }
    b = n_x+1+n_y+1+n_x+1;
    x[b] = subset->minx; y[b] = subset->maxy; z[b] = 0;
    for (i=1; i<=n_y; i++) {
        x[b+i] = subset->minx;
        y[b+i] = subset->maxy - (double) i * y_step;
        z[b+i] = 0;
    }
    
    OCTTransform(ct, n_points, x, y, z);
    GDALGCPTransform(transformer, TRUE, n_points, x, y, z, success);
    
    minx = (int) floor(eoxs_array_min(n_points, x));
    maxx = (int) ceil(eoxs_array_max(n_points, x));
    miny = (int) floor(eoxs_array_min(n_points, y));
    maxy = (int) ceil(eoxs_array_max(n_points, y));
    
    out_rect->x_off = minx;
    out_rect->y_off = miny;
    out_rect->x_size = maxx - minx + 1;
    out_rect->y_size = maxy - miny + 1;
    
    free(gcp_proj_wkt);
    free(x); free(y); free(z); free(success);
    eoxs_destroy_referenceable_grid_transformer(transformer);
    
    return 1;
}

int eoxs_create_rectified_vrt(GDALDatasetH ds, const char *vrt_filename, int srid) {
    GDALDatasetH vrt_ds;
    OGRSpatialReferenceH dst_srs;
    char *dst_srs_wkt;
    int free_dst_srs_wkt;
    
    void *transformer;
    GDALWarpOptions *warp_options;
    
    if (!ds) return 0;

    if (srid != 0) {
        dst_srs = OSRNewSpatialReference("");
        OSRImportFromEPSG(dst_srs, srid);
        OSRExportToWkt(dst_srs, &dst_srs_wkt);
        OSRRelease(dst_srs);
        free_dst_srs_wkt = TRUE;
    } else {
        dst_srs_wkt = (char*)GDALGetGCPProjection(ds);
        free_dst_srs_wkt = FALSE;
    }
    
    transformer = GDALCreateGenImgProjTransformer(
        ds,                       // source dataset
        NULL,                     // source projection WKT -> read from dataset 
        NULL,                     // destination dataset
        dst_srs_wkt,              // destination projection WKT
        TRUE,                     // use GCPs
        0.0,                      // ignored
        1                         // use interpolation order 1
    );
    
    if (!transformer) {
        if (free_dst_srs_wkt) free(dst_srs_wkt);
        return 0;
    }
    
    warp_options = GDALCreateWarpOptions();
    //warp_options->eResampleAlg = GRA_NearestNeighbour;
    warp_options->pTransformerArg = transformer;
    
    vrt_ds = GDALAutoCreateWarpedVRT(
        ds,                       // source dataset,
        NULL,                     // source projection WKT
        dst_srs_wkt,              // destination projection WKT,
        GRA_NearestNeighbour,     // resample algorithm
        0.0,                      // choose exact calculation
        warp_options              // warp options
    );
    
    if (!vrt_ds) {
        GDALDestroyGenImgProjTransformer(transformer);
        GDALDestroyWarpOptions(warp_options);
        if (free_dst_srs_wkt) free(dst_srs_wkt);
        return 0;
    }
    
    GDALSetDescription(vrt_ds, vrt_filename);
    
    // clean up
    GDALClose(vrt_ds);
    GDALDestroyGenImgProjTransformer(transformer);
    GDALDestroyWarpOptions(warp_options);
    if (free_dst_srs_wkt) free(dst_srs_wkt);
    
    return 1;
}
