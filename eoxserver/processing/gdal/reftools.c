/*
 *-----------------------------------------------------------------------------
 * $Id$
 *
 * Project: EOxServer <http://eoxserver.org>
 * Authors: Stephan Krause <stephan.krause@eox.at>
 *          Martin Paces <martin.paces@eox.at>
 *
 *-----------------------------------------------------------------------------
 * Copyright (C) 2011 EOX IT Services GmbH
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
 * copies of the Software, and to permit persons to whom the Software is 
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies of this Software or works derived from this Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *-----------------------------------------------------------------------------
*/
#include <stdio.h>
#include <string.h>

#include <gdal/gdal.h>
#include <gdal/gdal_alg.h>
#include <gdal/gdalwarper.h>
#include <gdal/ogr_srs_api.h>
#include <gdal/cpl_string.h>

/******************************************************************************/
/******************************************************************************/

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

/******************************************************************************/
/******************************************************************************/

void eoxs_destroy_footprint(eoxs_footprint *fp) {
    free(fp->x);
    free(fp->y);
    free(fp);
}

void eoxs_free_string(char* str)
{
    free(str);
}

void *eoxs_create_referenceable_grid_transformer(GDALDatasetH ds, const char *method) {
    int gcp_count;
    const GDAL_GCP *gcps;

    if (!ds || !method) return NULL;
    
    gcp_count = GDALGetGCPCount(ds);
    gcps = GDALGetGCPs(ds);

    if (EQUAL(method, "TPS")) {
        return GDALCreateTPSTransformer(gcp_count, gcps, FALSE);
    }
    else if (EQUAL(method, "GCP")) {
        return GDALCreateGCPTransformer(gcp_count, gcps, /* order */ 0, FALSE);
    }
    /* requires "tolerance" arg
     * else if (EQUAL(method, "GCP_refined")) {
        //return GDALCreateGCPRefineTransformer(gcp_count, gcps, 0, FALSE, 
    }*/
    else {
        return NULL;
    }
}

CPLErr eoxs_calculate_footprint(GDALDatasetH ds, const char *method, eoxs_footprint **out_footprint) {
    void *transformer;
    int x_size, y_size;
    double *x, *y, *z;

    int x_e, y_e;
    size_t n_points;
    int *success;
    int i;

    if (!ds) {
        CPLError(CE_Failure, CPLE_ObjectNull, "No dataset passed.");
        return CE_Failure;
    }

    else if ( 0 == GDALGetGCPCount(ds) ) {
        CPLError(CE_Failure, CPLE_IllegalArg, "The given dataset has no GCPs.");
        return CE_Failure; 
    }

    else if ( '\0' == GDALGetGCPProjection(ds)[0] ) {
        CPLError(CE_Failure, CPLE_IllegalArg, "The given dataset has no GCP projection.");
        return CE_Failure; 
    }

#ifdef DEBUG 
    { // debug - print the GCPs 
        printf("\nFootprint Source GCPs:"); 
        int i ; 
        char * dlm = "" ;
        const GDAL_GCP* gcp = GDALGetGCPs(ds);
        OGRSpatialReferenceH sr = OSRNewSpatialReference( GDALGetGCPProjection(ds) ) ;
        printf("\nFootprint Source GCPs:\n"); 
        if ( OGRERR_NONE == OSRAutoIdentifyEPSG( sr ) )  
            printf("SRID=%s;",OSRGetAuthorityCode(sr,NULL)) ; 
        else
            printf("%s\n",GDALGetGCPProjection(ds)) ;
        OSRDestroySpatialReference( sr ); 
        printf("MULTIPOINT(") ; 
        for ( i = 0 ; i < GDALGetGCPCount(ds) ; ++i ) 
        { 
            printf("%s%g %g",dlm,gcp[i].dfGCPX,gcp[i].dfGCPY) ; dlm = ", " ; 
        } 
        printf(")\n\n") ;
    }
#endif /* DEBUG */
 

    x_size = GDALGetRasterXSize(ds);
    y_size = GDALGetRasterYSize(ds);

    transformer = eoxs_create_referenceable_grid_transformer(ds, method);

    if (!transformer) {
        if (CPLGetLastErrorMsg() == NULL) {
            CPLError(CE_Failure, CPLE_OutOfMemory, "Failed to create GCP transformer.");
        }
        return CE_Failure; 
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

    /* for TPS and GCP methods returns always true */
    GDALUseTransformer(transformer, FALSE, n_points, x, y, z, success);

    // discard unused information
    free(z);
    free(success);
    GDALDestroyTransformer(transformer);

    *out_footprint = malloc(sizeof(eoxs_footprint));
    (*out_footprint)->n_points = n_points;
    (*out_footprint)->x = x;
    (*out_footprint)->y = y;

#ifdef DEBUG 
    { // debug - print the calculated footprint
        int i ; 
        char * dlm = "" ;
        printf("\nFootprint:\n"); 
        printf("SRID=%d;POLYGON ((",4326); 
        for ( i = 0 ; i < n_points ; ++i ) 
        { 
            printf("%s%g %g",dlm,x[i],y[i]) ; dlm = ", " ; 
        } 
        printf("%s%g %g))\n\n",dlm,x[0],y[0]) ; dlm = ", " ; 
    }
#endif /* DEBUG */

    return CE_None;
}

CPLErr eoxs_get_footprint_wkt(GDALDatasetH ds, const char *method, char **out_wkt) {
    eoxs_footprint *fp;
    char buffer[512];
    int i, maxlen;
    CPLErr ret;
    *out_wkt = NULL;

    if ((ret = eoxs_calculate_footprint(ds, method, &fp)) != CE_None) {
        return ret;
    }

    maxlen = (fp->n_points + 1) * 100 + sizeof("POLYGON(())");

    *out_wkt = calloc(maxlen, sizeof(char));

    if (!*out_wkt) {
        eoxs_destroy_footprint(fp);
        CPLError(CE_Failure, CPLE_OutOfMemory, "Error allocating memory.");
        return CE_Failure;
    }
    snprintf(*out_wkt, maxlen, "POLYGON((");

    for (i = 0; i < fp->n_points; ++i) {
        snprintf(buffer, sizeof(buffer), "%f %f", fp->x[i], fp->y[i]);
        if(i != 0) {
            CPLStrlcat(*out_wkt, ",", maxlen);
        }
        CPLStrlcat(*out_wkt, buffer, maxlen);
    }

    snprintf(buffer, sizeof(buffer), ",%f %f", fp->x[0], fp->y[0]);
    CPLStrlcat(*out_wkt, buffer, maxlen);
    CPLStrlcat(*out_wkt, "))", maxlen);

    // clean up
    eoxs_destroy_footprint(fp);

    return CE_None;
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
    
    GDALUseTransformer(transformer, FALSE, 4, x, y, z, success);
    
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

CPLErr eoxs_rect_from_subset(GDALDatasetH ds, eoxs_subset *subset, const char *method, eoxs_rect *out_rect) {
    void *transformer;
    
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
    
    if (!ds) {
        CPLError(CE_Failure, CPLE_ObjectNull, "No dataset passed.");
        return CE_Failure;
    }

    else if ( 0 == GDALGetGCPCount(ds) ) {
        CPLError(CE_Failure, CPLE_IllegalArg, "The given dataset has no GCPs.");
        return CE_Failure; 
    }

    else if ( '\0' == GDALGetGCPProjection(ds)[0] ) {
        CPLError(CE_Failure, CPLE_IllegalArg, "The given dataset has no GCP projection.");
        return CE_Failure; 
    }

#ifdef DEBUG 
    { // debug - print the GCPs  
        int i ; 
        char * dlm = "" ;
        const GDAL_GCP* gcp = GDALGetGCPs(ds);
        OGRSpatialReferenceH sr = OSRNewSpatialReference( GDALGetGCPProjection(ds) ) ;
        printf("\nSubsetting Source GCPs:\n"); 
        if ( OGRERR_NONE == OSRAutoIdentifyEPSG( sr ) )  
            printf("SRID=%s;",OSRGetAuthorityCode(sr,NULL)) ; 
        else
            printf("%s\n",GDALGetGCPProjection(ds)) ;
        OSRDestroySpatialReference( sr ); 
        printf("MULTIPOINT(") ; 
        for ( i = 0 ; i < GDALGetGCPCount(ds) ; ++i ) 
        { 
            printf("%s%g %g",dlm,gcp[i].dfGCPX,gcp[i].dfGCPY) ; dlm = ", " ; 
        } 
        printf(")\n\n") ;
    }
#endif /* DEBUG */
    
    ds_x_size = GDALGetRasterXSize(ds);
    ds_y_size = GDALGetRasterYSize(ds);
    
    transformer = eoxs_create_referenceable_grid_transformer(ds, method);
    
    if (!transformer) {
        if (CPLGetLastErrorMsg() == NULL) {
            CPLError(CE_Failure, CPLE_OutOfMemory, "Failed to create GCP transformer.");
        }
        return CE_Failure; 
    }
    
    gcp_srs = OSRNewSpatialReference( GDALGetGCPProjection(ds) );
    subset_srs = OSRNewSpatialReference("");
    OSRImportFromEPSG(subset_srs, subset->srid);
    
    ct = OCTNewCoordinateTransformation(subset_srs, gcp_srs);
    if (!ct) {
        if (CPLGetLastErrorMsg() == NULL) {
            CPLError(CE_Failure, CPLE_OutOfMemory, "Failed to create coordinate transformer.");
        }
        GDALDestroyTransformer(transformer);
        OSRDestroySpatialReference( gcp_srs ); 
        OSRDestroySpatialReference( subset_srs ); 
        return CE_Failure;
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

#ifdef DEBUG 
    { // debug - print the selection polygon
        int i ; 
        char * dlm = "" ;
        printf("\nSubseting - Selection Polygon:\n"); 
        printf("SRID=%d;POLYGON ((",subset->srid); 
        for ( i = 0 ; i < n_points ; ++i ) 
        { 
            printf("%s%g %g",dlm,x[i],y[i]) ; dlm = ", " ; 
        } 
        printf("%s%g %g))\n\n",dlm,x[0],y[0]) ; dlm = ", " ; 
    }
#endif /* DEBUG */

    OCTTransform(ct, n_points, x, y, z);
    GDALUseTransformer(transformer, TRUE, n_points, x, y, z, success);
    
    minx = (int) floor(eoxs_array_min(n_points, x));
    maxx = (int) ceil(eoxs_array_max(n_points, x));
    miny = (int) floor(eoxs_array_min(n_points, y));
    maxy = (int) ceil(eoxs_array_max(n_points, y));
    
    out_rect->x_off = minx;
    out_rect->y_off = miny;
    out_rect->x_size = maxx - minx + 1;
    out_rect->y_size = maxy - miny + 1;
    
    free(x); free(y); free(z); free(success);
    GDALDestroyTransformer(transformer);
    OCTDestroyCoordinateTransformation( ct ); 
    OSRDestroySpatialReference( gcp_srs ); 
    OSRDestroySpatialReference( subset_srs ); 
    
    return CE_None;
}

CPLErr eoxs_create_rectified_vrt(GDALDatasetH ds, const char *vrt_filename, int srid) {
    GDALDatasetH vrt_ds;
    OGRSpatialReferenceH dst_srs;
    char *dst_srs_wkt;
    int free_dst_srs_wkt;
    
    void *transformer;
    GDALWarpOptions *warp_options;
    
    if (!ds) {
        CPLError(CE_Failure, CPLE_ObjectNull, "No dataset passed.");
        return CE_Failure;
    }

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
        if (CPLGetLastErrorMsg() == NULL) {
            CPLError(CE_Failure, CPLE_OutOfMemory, "Failed to create image projection transformer.");
        }
        if (free_dst_srs_wkt) free(dst_srs_wkt);
        return CE_Failure;
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
        if (CPLGetLastErrorMsg() == NULL) {
            CPLError(CE_Failure, CPLE_FileIO, "Failed to created warped VRT.");
        }
        GDALDestroyGenImgProjTransformer(transformer);
        GDALDestroyWarpOptions(warp_options);
        if (free_dst_srs_wkt) free(dst_srs_wkt);
        return CE_Failure;
    }
    
    GDALSetDescription(vrt_ds, vrt_filename);
    
    // clean up
    GDALClose(vrt_ds);
    GDALDestroyGenImgProjTransformer(transformer);
    GDALDestroyWarpOptions(warp_options);
    if (free_dst_srs_wkt) free(dst_srs_wkt);
    
    return CE_None;
}
