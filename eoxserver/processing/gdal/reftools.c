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

#include <gdal.h>
#include <gdal_alg.h>
#include <gdalwarper.h>
#include <ogr_srs_api.h>
#include <cpl_string.h>


/******************************************************************************/
/* NOTE: define -DUSE_GDAL_EOX_EXTENSIONS to compile the EOX extended version */
/******************************************************************************/

/* GDAL Transformer methods */
#define METHOD_GCP 1  
#define METHOD_TPS 2  
#define METHOD_TPS_LSQ 3  

/* check that the required extensions are available */
#ifdef USE_GDAL_EOX_EXTENSIONS
#ifndef GDAL_USE_TPS2 
#error "The GDAL library does not provide required extensions!"
#endif 
#endif

/******************************************************************************/

typedef struct {
    size_t n_points;
    double *x;
    double *y;
} EOXS_FOOTPRINT;

typedef struct {
    int srid;
    double minx;
    double miny;
    double maxx;
    double maxy;
} EOXS_SUBSET;

typedef struct {
    int x_off;
    int y_off;
    int x_size;
    int y_size;
} EOXS_RECT;

typedef struct {
    int x_size;
    int y_size;
    double geotransform[6];
} EOXS_IMAGE_INFO;

/******************************************************************************/
/******************************************************************************/

/* check method and order */
CPLErr check_method_and_order(int method, int order)
{ 
    if (METHOD_GCP==method) 
    { 
        if (( order < 0 )||( order > 3 ))
        { 
            CPLError(CE_Failure,CPLE_IllegalArg,"Invalid polynomial order! ORDER=%d",order); 
            return CE_Failure;
        }
    } 
#ifdef USE_GDAL_EOX_EXTENSIONS
    else if ((METHOD_TPS==method)||(METHOD_TPS_LSQ==method ))
    { 
        if (( order < -1 )||( order > 3 ))
        { 
            CPLError(CE_Failure,CPLE_IllegalArg,"Invalid TPS augmenting polynomial order! ORDER=%d",order); 
            return CE_Failure;
        }
    }
#else 
    else if (METHOD_TPS==method)
    {
        if (order != 1)
        {
            CPLError(CE_Failure,CPLE_IllegalArg,"Invalid TPS augmenting polynomial order! ORDER=%d",order) ; 
            return CE_Failure;
        }
    }
    else if (METHOD_TPS_LSQ==method)
    { 
        CPLError(CE_Failure,CPLE_IllegalArg,"TPS_LSQ method not supported!") ;
        return CE_Failure;
    } 
#endif 
    else 
    { 
        CPLError(CE_Failure,CPLE_IllegalArg,"Invalid method! METHOD=%d",method) ;
        return CE_Failure;
    } 

    return CE_None ; 
} 


/* return 1 for extended or 0 for baseline version of GDAL */ 
int eoxs_is_extended( void ) 
{ 
#ifdef USE_GDAL_EOX_EXTENSIONS
    return 1 ; 
#else 
    return 0 ; 
#endif 
} 

void eoxs_destroy_footprint(EOXS_FOOTPRINT *fp) {
    free(fp->x);
    free(fp->y);
    free(fp);
}

void eoxs_free_string(char* str)
{
    free(str);
}

/******************************************************************************/

void *eoxs_create_referenceable_grid_transformer(GDALDatasetH ds, int method, int order)
{
    int gcp_count;
    const GDAL_GCP *gcps;

    if ( check_method_and_order(method,order) != CE_None ) return NULL ; 

    if (!ds) return NULL;
    
    gcp_count = GDALGetGCPCount(ds);
    gcps = GDALGetGCPs(ds);

#ifdef DEBUG 
    printf("GDAL Referenceable Transformer:\n") ; 
    printf("method = %d\n",method) ; 
    printf("order = %d\n",order) ; 
#endif 

    if ( METHOD_GCP == method ) 
    { 
        return GDALCreateGCPTransformer(gcp_count, gcps, order, FALSE);
    } 
    else if ( METHOD_TPS == method ) 
    { 
#ifdef USE_GDAL_EOX_EXTENSIONS
        return GDALCreateTPS2TransformerExt(gcp_count, gcps, FALSE, order);
#else 
        return GDALCreateTPSTransformer(gcp_count, gcps, FALSE);
#endif 
    } 
#ifdef USE_GDAL_EOX_EXTENSIONS
    else if ( METHOD_TPS_LSQ == method ) 
    { 
        return GDALCreateTPS2TransformerLSQGrid(gcp_count, gcps, FALSE, order, 0, 0);
    } 
#endif 
    else 
    { 
        return NULL ; 
    }
}

/******************************************************************************/

void *eoxs_create_gen_img_proj_transformer(
    GDALDatasetH ds_src, // mandatory 
    const char * srs_wkt_src, // can be NULL 
    GDALDatasetH ds_dst,     // can be NULL 
    const char * srs_wkt_dst, // can be NULL (if ds_dst provided)
    int method, 
    int order)
{
    void *transformer = NULL ;
    char ** topt = NULL ; 

#ifdef DEBUG 
    printf("GDAL Gen.Img. Transformer:\n") ; 
    printf("method = %d\n",method) ; 
    printf("order = %d\n",order) ; 
#endif 

    if ( check_method_and_order(method,order) != CE_None ) return NULL ; 

    // SET TRANSFOMER OPTIONS
    
    // destination projection WKT
    if ( srs_wkt_src ) 
        topt = CSLSetNameValue( topt, "SRC_SRS", srs_wkt_src );
    
    // source projection WKT
    if ( srs_wkt_dst ) 
        topt = CSLSetNameValue( topt, "DST_SRS", srs_wkt_dst ); 

    // use GCPs from the source dataset (TRUE set by default)
    //topt = CSLSetNameValue( topt, "GCPS_OK", "TRUE" ); 

    // method specific options 
    if (METHOD_GCP==method) 
    { 
        topt = CSLSetNameValue( topt, "METHOD", "GCP_POLYNOMIAL" ); // set method to GCP polynomial interpolation

        if ( order > 0 ) 
            topt = CSLSetNameValue( topt, "MAX_GCP_ORDER", CPLSPrintf("%d",order) ); // set max. polymomial order
    } 
#ifdef USE_GDAL_EOX_EXTENSIONS
    else if ((METHOD_TPS==method)||(METHOD_TPS_LSQ==method))
    { 
        topt = CSLSetNameValue( topt, "METHOD", "GCP_TPS2" ); // set method to GCP Thin Plate Spline v2 interpolation 
        topt = CSLSetNameValue( topt, "TPS2_AP_ORDER", CPLSPrintf("%d",order) ); // augmenting polynomial order 
    
        if (METHOD_TPS_LSQ==method)
        { 
            topt = CSLSetNameValue( topt, "TPS2_LSQ_GRID", "1" ); // use alternative rectangular grid 
            topt = CSLSetNameValue( topt, "TPS2_LSQ_GRID_NX", "0" ); // x grid size (0 means default)
            topt = CSLSetNameValue( topt, "TPS2_LSQ_GRID_NY", "0" ); // y grid size (0 means default)
        } 
    } 
#else
    else if (METHOD_TPS==method)
    { 
        topt = CSLSetNameValue( topt, "METHOD", "GCP_TPS" ); // set method to GCP Thin Plate Spline interpolation 
    } 
#endif 
    else return NULL ; 

    // CREATE TRANSFOMER 
    transformer = GDALCreateGenImgProjTransformer2(
        ds_src,  // source dataset 
        ds_dst,  // destination dataset
        topt     // trasformer options
    ); 

    // DISCARD TRANSFOMER OPTIONS 
    CSLDestroy( topt );

    return transformer ; 
} 

/******************************************************************************/

CPLErr eoxs_calculate_footprint(GDALDatasetH ds, int method, int order, EOXS_FOOTPRINT **out_footprint) {
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

    transformer = eoxs_create_referenceable_grid_transformer(ds, method, order);

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

    *out_footprint = malloc(sizeof(EOXS_FOOTPRINT));
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

CPLErr eoxs_get_footprint_wkt(GDALDatasetH ds, int method, int order, char **out_wkt) {
    EOXS_FOOTPRINT *fp;
    char buffer[512];
    int i, maxlen;
    CPLErr ret;
    *out_wkt = NULL;

    if ((ret = eoxs_calculate_footprint(ds, method, order, &fp)) != CE_None) {
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
    EOXS_SUBSET *subset,
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

CPLErr eoxs_rect_from_subset(GDALDatasetH ds, EOXS_SUBSET *subset, int method, int order, EOXS_RECT *out_rect) {
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
    
    transformer = eoxs_create_referenceable_grid_transformer(ds, method, order);
    
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

CPLErr eoxs_create_rectified_vrt(GDALDatasetH ds, const char *vrt_filename,
                            int srid, // TODO: make it work with srs_wkt 
                            GDALResampleAlg eResampleAlg, 
                            double dfWarpMemoryLimit, 
                            double dfMaxError,
                            int method, int order)
{
    GDALDatasetH vrt_ds;
    OGRSpatialReferenceH dst_srs;
    char *dst_srs_wkt;
    int free_dst_srs_wkt;
    
    void *transformer;
    GDALWarpOptions *warp_options;

    CPLErr ret ; 
    int x_size,y_size;
    double geotransform[6];

    if ( check_method_and_order(method,order) != CE_None ) return CE_Failure; 
    
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
    
    transformer = eoxs_create_gen_img_proj_transformer( 
        ds,                       // source dataset
        NULL,                     // source projection WKT -> read from dataset 
        NULL,                     // destination dataset
        dst_srs_wkt,              // destination projection WKT
        method, order 
    );
    
    if (!transformer) {
        if (CPLGetLastErrorMsg() == NULL) {
            CPLError(CE_Failure, CPLE_OutOfMemory, "Failed to create image projection transformer.");
        }
        if (free_dst_srs_wkt) free(dst_srs_wkt);
        return CE_Failure;
    }

    // guess the size of the created image

    ret = GDALSuggestedWarpOutput(ds, GDALGenImgProjTransform, 
                transformer, geotransform, &x_size, &y_size );

    if ( ret != CE_None ) 
    {
        GDALDestroyGenImgProjTransformer(transformer);
        return ret ;  
    }

    // update the transformer to include the output geo-transform 
    
    GDALSetGenImgProjTransformerDstGeoTransform( transformer, geotransform ); 

    // set warp options 
    
    warp_options = GDALCreateWarpOptions();

    warp_options->dfWarpMemoryLimit = dfWarpMemoryLimit ;   // warp memory limit 
    warp_options->eResampleAlg = eResampleAlg ;             // resampling method
    warp_options->pfnTransformer = GDALGenImgProjTransform ;// specific transform function
    warp_options->pTransformerArg = transformer;            // pointer to the transfomer 
    warp_options->hSrcDS = ds ;                             // source dataset 

    { 
        int i , j , nb ; 

        // bands setup
        warp_options->nBandCount = nb = GDALGetRasterCount( ds );
        warp_options->panSrcBands = (int*)CPLMalloc(sizeof(int) * nb );
        warp_options->panDstBands = (int*)CPLMalloc(sizeof(int) * nb );

        for( i = 0; i < nb ; i++ )
        {
            warp_options->panSrcBands[i] = i+1;
            warp_options->panDstBands[i] = i+1;
        }

        // handle no-data values alpha bands
        for( i = 0; i < nb ; i++ )
        { 
            GDALRasterBandH band = GDALGetRasterBand( ds, i+1 );
            int has_noda_value = FALSE ; 
            double v_nodata = GDALGetRasterNoDataValue( band, &has_noda_value ) ; 

            if ( has_noda_value ) 
            { 
                // if not yet allocated allocate the no-data vectors
            
                if( NULL == warp_options->padfSrcNoDataReal )
                { 
                    warp_options->padfSrcNoDataImag = (double*)CPLCalloc(nb,sizeof(double)) ; 
                    warp_options->padfSrcNoDataReal = (double*)CPLMalloc(sizeof(double)*nb) ; 

                    //NOTE: the 'magic constant' taken from the GDAL sources 
                    for ( j = 0 ; j < nb ; ++j ) 
                        warp_options->padfSrcNoDataReal[j] = -1.1e20;
                } 

                warp_options->padfSrcNoDataReal[i] = v_nodata ;
            } 

            if ( GDALGetRasterColorInterpretation(band) == GCI_AlphaBand )
            { 
                warp_options->nSrcAlphaBand = i+1 ; 
                warp_options->nDstAlphaBand = i+1 ; 
            } 
        } 
    } 

    // approximating transformation (desired as it makes warping really faster)
    if ( 0 < dfMaxError ) 
    { 
        warp_options->pTransformerArg =         // pointer to the transfomer
                GDALCreateApproxTransformer( 
                    warp_options->pfnTransformer,
                    warp_options->pTransformerArg, 
                    dfMaxError ) ; 
                    
        warp_options->pfnTransformer = GDALApproxTransform; // specific transform function

        // make sure the original transformer gets destroyed
        GDALApproxTransformerOwnsSubtransformer(
                warp_options->pTransformerArg, TRUE );
    }    

    // create the rectified (warped) VRT
    // NOTE: VRT dataset steels ownership of the warp_options->pfnTransformer !!!
    vrt_ds = GDALCreateWarpedVRT( ds, // source dataset
            x_size, y_size,     // image size 
            geotransform,       // geotransformation matrix
            warp_options ) ;    // warp options 

    if ( vrt_ds ) // SUCCESS 
    {
        // set some additional metadata
        GDALSetProjection( vrt_ds, dst_srs_wkt );
        GDALSetDescription( vrt_ds, vrt_filename );

        // close the dataset 
        GDALClose(vrt_ds); // NOTE: GDALClose() destroys the transformers!!!

        // NOTE: GDALClose() commits the actual file write. Check for any possible I/O errors!
        ret = CPLGetLastErrorType() ; 
    } 
    else    // FAILURE 
    {
        if (CPLGetLastErrorMsg() == NULL)
            CPLError(CE_Failure, CPLE_FileIO, "Failed to created warped VRT.");

        ret = CE_Failure;
    }
   
    // clean-up the mess 
    
    GDALDestroyWarpOptions( warp_options );
    if (free_dst_srs_wkt) free(dst_srs_wkt);

    return ret ;
}

/* Thin wrapper for GDALSuggestedWarpOutput which allows the setting of the order. */
CPLErr eoxs_suggested_warp_output(GDALDatasetH ds, 
                                  const char *src_wkt, /* can be NULL */
                                  const char *dst_wkt,
                                  int method, int order,
                                  EOXS_IMAGE_INFO* out) {

    CPLErr ret;
    void *transformer = eoxs_create_gen_img_proj_transformer( 
        ds, src_wkt, NULL, dst_wkt, method, order ) ; 

    if (!transformer) {
        return CE_Failure;
    }
    
    ret = GDALSuggestedWarpOutput(ds, GDALGenImgProjTransform, 
                                  transformer, 
                                  out->geotransform,
                                  &out->x_size, &out->y_size);

    // clean up
    GDALDestroyTransformer(transformer);

    return ret;
}


/* original source copied from gdalwarper.cpp - some mods have been made though */
CPLErr eoxs_reproject_image(GDALDatasetH hSrcDS,
                            const char *pszSrcWKT, 
                            GDALDatasetH hDstDS,
                            const char *pszDstWKT,
                            GDALResampleAlg eResampleAlg, 
                            double dfWarpMemoryLimit, 
                            double dfMaxError,
                            int method, int order) 
{
    
    GDALWarpOptions *psWOptions;

/* -------------------------------------------------------------------- */
/*      Setup a reprojection based transformer.                         */
/* -------------------------------------------------------------------- */
    void *hTransformArg = eoxs_create_gen_img_proj_transformer( 
            hSrcDS, pszSrcWKT, hDstDS, pszDstWKT, method, order ) ;

    if( hTransformArg == NULL )
        return CE_Failure;

/* -------------------------------------------------------------------- */
/*      Create a copy of the user provided options, or a defaulted      */
/*      options structure.                                              */
/* -------------------------------------------------------------------- */
    psWOptions = GDALCreateWarpOptions();
    psWOptions->eResampleAlg = eResampleAlg;
    psWOptions->dfWarpMemoryLimit = dfWarpMemoryLimit ;   // warp memory limit 

/* -------------------------------------------------------------------- */
/*      Set transform.                                                  */
/* -------------------------------------------------------------------- */
    if( dfMaxError > 0.0 )
    {
        psWOptions->pTransformerArg = 
            GDALCreateApproxTransformer( GDALGenImgProjTransform, 
                                         hTransformArg, dfMaxError );

        psWOptions->pfnTransformer = GDALApproxTransform;
    }
    else
    {
        psWOptions->pfnTransformer = GDALGenImgProjTransform;
        psWOptions->pTransformerArg = hTransformArg;
    }

/* -------------------------------------------------------------------- */
/*      Set file and band mapping.                                      */
/* -------------------------------------------------------------------- */
    int  iBand;

    psWOptions->hSrcDS = hSrcDS;
    psWOptions->hDstDS = hDstDS;

    if( psWOptions->nBandCount == 0 )
    {
        psWOptions->nBandCount = MIN(GDALGetRasterCount(hSrcDS),
                                     GDALGetRasterCount(hDstDS));
        
        psWOptions->panSrcBands = (int *) 
            CPLMalloc(sizeof(int) * psWOptions->nBandCount);
        psWOptions->panDstBands = (int *) 
            CPLMalloc(sizeof(int) * psWOptions->nBandCount);

        for( iBand = 0; iBand < psWOptions->nBandCount; iBand++ )
        {
            psWOptions->panSrcBands[iBand] = iBand+1;
            psWOptions->panDstBands[iBand] = iBand+1;
        }
    }

/* -------------------------------------------------------------------- */
/*      Set source nodata values if the source dataset seems to have    */
/*      any.                                                            */
/* -------------------------------------------------------------------- */
    for( iBand = 0; iBand < psWOptions->nBandCount; iBand++ )
    {
        GDALRasterBandH hBand = GDALGetRasterBand( hSrcDS, iBand+1 );
        int             bGotNoData = FALSE;
        double          dfNoDataValue;

        if (GDALGetRasterColorInterpretation(hBand) == GCI_AlphaBand)
        {
            psWOptions->nSrcAlphaBand = iBand + 1;
        }

        dfNoDataValue = GDALGetRasterNoDataValue( hBand, &bGotNoData );
        if( bGotNoData )
        {
            if( psWOptions->padfSrcNoDataReal == NULL )
            {
                int  ii;

                psWOptions->padfSrcNoDataReal = (double *) 
                    CPLMalloc(sizeof(double) * psWOptions->nBandCount);
                psWOptions->padfSrcNoDataImag = (double *) 
                    CPLMalloc(sizeof(double) * psWOptions->nBandCount);

                for( ii = 0; ii < psWOptions->nBandCount; ii++ )
                {
                    psWOptions->padfSrcNoDataReal[ii] = -1.1e20;
                    psWOptions->padfSrcNoDataImag[ii] = 0.0;
                }
            }

            psWOptions->padfSrcNoDataReal[iBand] = dfNoDataValue;
        }

        hBand = GDALGetRasterBand( hDstDS, iBand+1 );
        if (hBand && GDALGetRasterColorInterpretation(hBand) == GCI_AlphaBand)
        {
            psWOptions->nDstAlphaBand = iBand + 1;
        }
    }

/* -------------------------------------------------------------------- */
/*      Create a warp options based on the options.                     */
/* -------------------------------------------------------------------- */
    GDALWarpOperationH  hWarper = GDALCreateWarpOperation( psWOptions );
    CPLErr eErr = CE_Failure;

    if( hWarper )
        eErr = GDALChunkAndWarpImage( hWarper, 0, 0, 
                                      GDALGetRasterXSize(hDstDS),
                                      GDALGetRasterYSize(hDstDS) );

/* -------------------------------------------------------------------- */
/*      Cleanup.                                                        */
/* -------------------------------------------------------------------- */
    GDALDestroyGenImgProjTransformer( hTransformArg );

    if( dfMaxError > 0.0 )
        GDALDestroyApproxTransformer( psWOptions->pTransformerArg );
        
    GDALDestroyWarpOptions( psWOptions );

    return eErr;
}
