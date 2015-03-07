/*------------------------------------------------------------------------------
! . File      : DFTGridWeights.c
! . Program   : pDynamo-1.9.0                           (http://www.pdynamo.org)
! . Copyright : CEA, CNRS, Martin J. Field (2007-2014)
! . License   : CeCILL French Free Software License     (http://www.cecill.info)
!-----------------------------------------------------------------------------*/
/*==============================================================================
! . This module handles the DFT grid weights.
!=============================================================================*/

# include <math.h>

# include "Coordinates3.h"
# include "DFTGridWeights.h"
# include "Memory.h"

# define DFTGRIDWEIGHTS_BECKE
# define DFTGRIDWEIGHTS_ATOMSIZES

/* . Nothing complicated done here until decide what to do about the grid. */

/*----------------------------------------------------------------------------------------------------------------------------------
! . Parameters.
!---------------------------------------------------------------------------------------------------------------------------------*/
/* . The polynomial order. */
# define NTRANS 10

/* . Pascal triangle parameters. */
const Real APASC           =    1.850069046020527e+00 ;
const Real XPASC[NTRANS+1] = {  1.000000000000000e+00 , 
                               -3.333333333333333e+00 ,
                                9.000000000000000e+00 ,
                              -17.142857142857142e+00 ,
                               23.333333333333332e+00 ,
                              -22.909090909090910e+00 ,
                               16.153846153846153e+00 ,
                               -8.000000000000000e+00 ,
                                2.647058823529412e+00 ,
                               -0.526315789473684e+00 ,
                                0.047619047619048e+00 } ;

/*==================================================================================================================================
! . Grid weights procedures.
!=================================================================================================================================*/
/*----------------------------------------------------------------------------------------------------------------------------------
! . Allocation.
!---------------------------------------------------------------------------------------------------------------------------------*/
DFTGridWeights *DFTGridWeights_Allocate ( const Coordinates3 *qcCoordinates3, const Real *radii )
{
    DFTGridWeights *self = NULL ;
    if ( ( qcCoordinates3 != NULL ) && ( qcCoordinates3->length0 > 0 ) )
    {
        auto Real chi, temp, xij, yij, zij ;
        auto Integer    ij, iqm, jqm, n ;
        self = ( DFTGridWeights * ) Memory_Allocate ( sizeof ( DFTGridWeights ) ) ;
        self->qcCoordinates3 = qcCoordinates3 ;
        n = qcCoordinates3->length0 ;
        /* . Allocation. */
        self->aij = Memory_Allocate_Array_Real_Initialize ( ( n * ( n - 1 ) ) / 2, 9999999999.0e+00 ) ;
        self->rij = Memory_Allocate_Array_Real_Initialize ( ( n * ( n - 1 ) ) / 2, 9999999999.0e+00 ) ;
        /* . Fill AIJ and RIJ. */
        for ( ij = 0, iqm = 0 ; iqm < n ; iqm++ )
        {
            for ( jqm = 0 ; jqm < iqm ; ij++, jqm++ )
            {
                Coordinates3_DifferenceRow ( qcCoordinates3, iqm, jqm, xij, yij, zij ) ;
                self->rij[ij] = 1.0e+00 / sqrt ( xij*xij + yij*yij + zij*zij ) ;
                chi  = radii[iqm] / radii[jqm] ;
                temp = ( chi - 1.0e+00 ) / ( chi + 1.0e+00 ) ;
                self->aij[ij] = temp / ( temp*temp - 1.0e+00 ) ;
                if ( self->aij[ij] >  0.5e+00 ) self->aij[ij] =  0.5e+00 ;
                if ( self->aij[ij] < -0.5e+00 ) self->aij[ij] = -0.5e+00 ;
            }
        }
    }
    return self ;
}

/*----------------------------------------------------------------------------------------------------------------------------------
! . Deallocation.
!---------------------------------------------------------------------------------------------------------------------------------*/
void DFTGridWeights_Deallocate ( DFTGridWeights **self )
{
    if ( (*self) != NULL )
    {
        Memory_Deallocate_Real ( &((*self)->aij) ) ;
        Memory_Deallocate_Real ( &((*self)->rij) ) ;
        Memory_Deallocate ( (*self) ) ;
    }
}

/*----------------------------------------------------------------------------------------------------------------------------------
! . Calculate the weight derivatives.
!---------------------------------------------------------------------------------------------------------------------------------*/
void DFTGridWeights_Derivatives ( const DFTGridWeights                *self             ,
                                  const Integer                        gridAtom         ,
                                  const Integer                        numberOfPoints   ,
                                  const Coordinates3                  *gridCoordinates3 ,
                                  const Real1DArray                   *gridWeights      ,
                                  const Real1DArray                   *eXC              ,
                                        Coordinates3                  *gradients3       ,
                                        DFTGridWeightsDerivativesWork *work             )
{
    if ( ( self != NULL ) && ( gridCoordinates3 != NULL ) && ( gridWeights != NULL ) && ( eXC != NULL ) && ( gradients3 != NULL ) && ( work != NULL ) )
    {
        auto Integer g, i, ii, ij, j, jj, k, m, n, t ;
        auto Real    aij, aji, dnu, dsum, dxg, dxi, dxj, dyg, dyi, dyj, dzg, dzi, dzj, ew, fac, ifac, mu, nu, nu2, 
                     p, rgX, rgY, rgZ, rij, snu, sum, tx, ty, tz, w, x, xi, xj, y, yi, yj, z, zi, zj ;
        auto Real   *A = work->A, *dAdm = work->dAdm, *R = work->R ;

        /* . Set some counters. */
        n = self->qcCoordinates3->length0 ;

        /* . Loop over points. */
        for ( g = 0 ; g < numberOfPoints ; g++ )
        {
            /* . Get information for the point. */
            Coordinates3_GetRow ( gridCoordinates3, g, rgX, rgY, rgZ ) ;
            w = Real1DArray_Item ( gridWeights, g ) ;

            /* . Calculate the distances between the atoms and the point. */
            for ( i = 0 ; i < n ; i++ )
            {
                Coordinates3_GetRow ( self->qcCoordinates3, i, x, y, z ) ;
                x -= rgX ; y -= rgY ; z -= rgZ ;
                A[i] = 1.0e+00 ;
                R[i] = sqrt ( x*x + y*y + z*z ) ;
            }

            /* . Initialize the derivative array. */
            for ( i = 0 ; i < ( n * n ) ; i++ ) dAdm[i] = 1.0e+00 ;

            /* . Double loop over atoms to get A. */
            for ( ij = 0, i = 0 ; i < n ; i++ )
            {
                for ( j = 0 ; j < i ; ij++, j++ )
                {
                    mu  = ( R[i] - R[j] ) * self->rij[ij] ;
                    nu  = mu + self->aij[ij] * ( 1.0e+00 - mu * mu ) ;
                    nu2 = nu * nu ;
                    dnu = 1.0e+00 ;
                    snu = nu      ;
                    for ( dsum = 0.0e+00, sum = 0.0e+00, t = 0 ; t <= NTRANS ; t++ )
                    {
                        dsum += XPASC[t] * dnu * ( Real ) ( 2 * t + 1 ) ;
                        sum  += XPASC[t] * snu ;
                        dnu  *= nu2 ;
                        snu  *= nu2 ;
	            }
                    aij = ( 0.5e+00 - APASC * sum ) ;
                    aji = ( 0.5e+00 + APASC * sum ) ;
                    A[i] *= aij ;
                    A[j] *= aji ;
                    dsum *= - APASC * ( 1.0e+00 - 2.0e+00 * self->aij[ij] * mu ) ;
                    for ( ii = i * n, jj = j * n, k = 0 ; k < n ; ii++, jj++, k++ )
                    {
                        if ( k == j ) dAdm[ii] *= dsum ;
                        else          dAdm[ii] *= aij  ;
                        if ( k == i ) dAdm[jj] *= dsum ;
                        else          dAdm[jj] *= aji  ;
                    }
                }
            }

            /* . Find the partitioning weight using the normalized A. */
            for ( sum = 0.0e+00, i = 0 ; i < n ; i++ ) sum += A[i] ;
            p = A[gridAtom] / sum ;

            /* . Find the integral value multiplied by the constant weight and divided by Anorm. */
            ew = Real1DArray_Item ( eXC, g ) * w / ( p * sum ) ;

            /* . Loop over the derivatives of A. */
            for ( i = 0, m = 0 ; i < n ; i++ )
            {
                Coordinates3_GetRow ( self->qcCoordinates3, i, xi, yi, zi ) ;
                if ( i == gridAtom ) fac = ew * ( 1.0e+00 - p ) ;
                else                 fac = - ew * p ;
                for ( j = 0 ; j < n ; j++, m++ )
                {
                    if ( i == j ) continue ;
                    Coordinates3_GetRow ( self->qcCoordinates3, j, xj, yj, zj ) ;
                    if ( i > j ) ij = ( i * ( i - 1 ) ) / 2 + j ;
                    else         ij = ( j * ( j - 1 ) ) / 2 + i ;
                    rij = self->rij[ij] ;
                    mu  = ( R[i] - R[j] ) * rij ;
                    /* . Grid point derivatives. */
                    dxi =   ( xi - rgX ) * rij / R[i] ;
                    dyi =   ( yi - rgY ) * rij / R[i] ;
                    dzi =   ( zi - rgZ ) * rij / R[i] ;
                    dxj = - ( xj - rgX ) * rij / R[j] ;
                    dyj = - ( yj - rgY ) * rij / R[j] ;
                    dzj = - ( zj - rgZ ) * rij / R[j] ;
                    dxg = - ( dxi + dxj ) ;
                    dyg = - ( dyi + dyj ) ;
                    dzg = - ( dzi + dzj ) ;
                    /* . Atom derivatives. */
                    tx   = ( xi - xj ) * mu * rij * rij ;
                    ty   = ( yi - yj ) * mu * rij * rij ;
                    tz   = ( zi - zj ) * mu * rij * rij ;
                    dxi -= tx ;
                    dyi -= ty ;
                    dzi -= tz ;
                    dxj += tx ;
                    dyj += ty ;
                    dzj += tz ;
                    /* . Contributions. */
                    ifac = dAdm[m] * fac ;
                    Coordinates3_IncrementRow ( gradients3, i       , ifac * dxi, ifac * dyi, ifac * dzi ) ;
                    Coordinates3_IncrementRow ( gradients3, j       , ifac * dxj, ifac * dyj, ifac * dzj ) ;
                    Coordinates3_IncrementRow ( gradients3, gridAtom, ifac * dxg, ifac * dyg, ifac * dzg ) ;
                }
            }
        }
    }
}

/*----------------------------------------------------------------------------------------------------------------------------------
! . Calculate a weight.
!---------------------------------------------------------------------------------------------------------------------------------*/
double DFTGridWeights_Weight ( DFTGridWeights *self, const Integer iqm, const Real *rg, Real *psmu, Real *rtemp )
{
    Real w = 1.0e+00 ;
    if ( ( self != NULL ) && ( rg != NULL ) && ( psmu != NULL ) && ( rtemp !=NULL ) )
    {
        auto Real accum, x, xmu, xmuij, xmuijn, xmuij2, y, z ;
        auto Integer    i, ij, j, t ;

        /* . Calculate the distances between the atoms and the points. */
        for ( i = 0 ; i < self->qcCoordinates3->length0 ; i++ )
        {
            Coordinates3_GetRow ( self->qcCoordinates3, i, x, y, z ) ;
            x -= rg[0] ; y -= rg[1] ; z -= rg[2] ;
            psmu[i]  = 1.0e+00 ;
            rtemp[i] = sqrt ( x*x + y*y + z*z ) ;
        }

        /* . Double loop over atoms to get psmu. */
        for ( ij = 0, i = 0 ; i < self->qcCoordinates3->length0 ; i++ )
        {
            for ( j = 0 ; j < i ; ij++, j++ )
            {
                xmu    = ( rtemp[i] - rtemp[j] ) * self->rij[ij] ;
                xmuij  = xmu + self->aij[ij] * ( 1.0e+00 - xmu * xmu ) ;
                xmuij2 = xmuij * xmuij ;
                xmuijn = xmuij ;
                for ( accum = 0.0e+00, t = 0 ; t <= NTRANS ; t++ )
                {
                    accum  += XPASC[t] * xmuijn ;
                    xmuijn *= xmuij2 ;
	        }
                psmu[i] *= ( 0.5e+00 - APASC * accum ) ;
                psmu[j] *= ( 0.5e+00 + APASC * accum ) ;
            }
        }

        /* . Find the weight using the normalized psmu. */
        for ( accum = 0.0e+00, i = 0 ; i < self->qcCoordinates3->length0 ; i++ ) accum += psmu[i] ;
        w = psmu[iqm] / accum ;
    }
    return w ;
}

/*==================================================================================================================================
! . Grid weights derivatives work procedures.
!=================================================================================================================================*/
/*----------------------------------------------------------------------------------------------------------------------------------
! . Allocation.
!---------------------------------------------------------------------------------------------------------------------------------*/
DFTGridWeightsDerivativesWork *DFTGridWeightsDerivativesWork_Allocate ( const DFTGridWeights *gridWeights, Status *status )
{
    DFTGridWeightsDerivativesWork *self = NULL ;
    if ( ( gridWeights != NULL ) && ( gridWeights->qcCoordinates3->length0 > 0 ) )
    {
        auto Integer n ;
        n     = gridWeights->qcCoordinates3->length0 ;
        self  = ( DFTGridWeightsDerivativesWork * ) Memory_Allocate ( sizeof ( DFTGridWeightsDerivativesWork ) ) ;
        if ( self != NULL )
        {
            self->A    = Memory_Allocate_Array_Real ( n ) ;
            self->R    = Memory_Allocate_Array_Real ( n ) ;
            self->dAdm = Memory_Allocate_Array_Real ( n * n ) ;
            if ( ( self->A == NULL ) || ( self->R == NULL ) || ( self->dAdm == NULL ) ) DFTGridWeightsDerivativesWork_Deallocate ( &self ) ;
        }
        if ( self == NULL ) Status_Set ( status, Status_MemoryAllocationFailure ) ;
    }
    return self ;
}

/*----------------------------------------------------------------------------------------------------------------------------------
! . Deallocation.
!---------------------------------------------------------------------------------------------------------------------------------*/
void DFTGridWeightsDerivativesWork_Deallocate ( DFTGridWeightsDerivativesWork **self )
{
    if ( (*self) != NULL )
    {
        Memory_Deallocate_Real ( &((*self)->A   ) ) ;
        Memory_Deallocate_Real ( &((*self)->R   ) ) ;
        Memory_Deallocate_Real ( &((*self)->dAdm) ) ;
        Memory_Deallocate ( (*self) ) ;
    }
}
