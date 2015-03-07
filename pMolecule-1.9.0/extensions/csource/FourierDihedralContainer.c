/*------------------------------------------------------------------------------
! . File      : FourierDihedralContainer.c
! . Program   : pDynamo-1.9.0                           (http://www.pdynamo.org)
! . Copyright : CEA, CNRS, Martin J. Field (2007-2014)
! . License   : CeCILL French Free Software License     (http://www.cecill.info)
!-----------------------------------------------------------------------------*/
/*==============================================================================
!=============================================================================*/

# include <math.h>
# include <stdlib.h>

# include "FourierDihedralContainer.h"
# include "Memory.h"

/*------------------------------------------------------------------------------
! . Local procedures.
!-----------------------------------------------------------------------------*/
static Integer FourierDihedralTerm_Compare ( const void *vterm1, const void *vterm2 ) ;

/*==============================================================================
! . Procedures.
!=============================================================================*/
/*------------------------------------------------------------------------------
! . Activate terms.
!-----------------------------------------------------------------------------*/
void FourierDihedralContainer_ActivateTerms ( FourierDihedralContainer *self )
{
    if ( self != NULL )
    {
        auto Integer i ;
	for ( i = 0 ; i < self->nterms ; i++ ) self->terms[i].QACTIVE = True ;
    }
}

/*------------------------------------------------------------------------------
! . Allocation.
!-----------------------------------------------------------------------------*/
FourierDihedralContainer *FourierDihedralContainer_Allocate ( const Integer nterms, const Integer nparameters )
{
    FourierDihedralContainer *self = NULL ;
    if ( ( nterms != 0 ) && ( nparameters != 0 ) )
    {
        Integer i ;
	self = ( FourierDihedralContainer * ) Memory_Allocate ( sizeof ( FourierDihedralContainer ) ) ;
        self->QSORTED     = False       ;
	self->nterms      = nterms      ;
	self->nparameters = nparameters ;
	self->terms	  = ( FourierDihedral * )          Memory_Allocate_Array ( nterms,      sizeof ( FourierDihedral )          ) ;
	self->parameters  = ( FourierDihedralParameter * ) Memory_Allocate_Array ( nparameters, sizeof ( FourierDihedralParameter ) ) ;
	/* . Make all terms inactive. */
	for ( i = 0 ; i < nterms ; i++ ) self->terms[i].QACTIVE = False ;
    }
    return self ;
}

/*------------------------------------------------------------------------------
! . Cloning.
!-----------------------------------------------------------------------------*/
FourierDihedralContainer *FourierDihedralContainer_Clone ( const FourierDihedralContainer *self )
{
    FourierDihedralContainer *new = NULL ;
    if ( self != NULL )
    {
        auto Integer i ;
        new = FourierDihedralContainer_Allocate ( self->nterms, self->nparameters ) ;
        for ( i = 0 ; i < self->nterms ; i++ )
        {
            new->terms[i].QACTIVE = self->terms[i].QACTIVE ;
            new->terms[i].atom1   = self->terms[i].atom1   ;
            new->terms[i].atom2   = self->terms[i].atom2   ;
            new->terms[i].atom3   = self->terms[i].atom3   ;
            new->terms[i].atom4   = self->terms[i].atom4   ;
            new->terms[i].type    = self->terms[i].type    ;
        }
        for ( i = 0 ; i < self->nparameters ; i++ )
        {
            new->parameters[i].fc       = self->parameters[i].fc       ;
            new->parameters[i].period   = self->parameters[i].period   ;
            new->parameters[i].phase    = self->parameters[i].phase    ;
            new->parameters[i].cosphase = self->parameters[i].cosphase ;
            new->parameters[i].sinphase = self->parameters[i].sinphase ;
        }
        new->QSORTED = self->QSORTED ;
    }
    return new ;
}

/*------------------------------------------------------------------------------
! . Deactivate terms between fixed atoms.
! . Already deactivated terms are not affected.
!-----------------------------------------------------------------------------*/
void FourierDihedralContainer_DeactivateFixedAtomTerms ( FourierDihedralContainer *self, Selection *fixedatoms )
{
    if ( ( self != NULL ) && ( fixedatoms != NULL ) )
    {
        auto Integer i, n ;
        n = FourierDihedralContainer_UpperBound ( self ) ;
        Selection_MakeFlags ( fixedatoms, n ) ;
	for ( i = 0 ; i < self->nterms ; i++ )
	{
            if ( self->terms[i].QACTIVE )
            {
                self->terms[i].QACTIVE = ! ( fixedatoms->flags[self->terms[i].atom1] &&
                                             fixedatoms->flags[self->terms[i].atom2] &&
                                             fixedatoms->flags[self->terms[i].atom3] &&
                                             fixedatoms->flags[self->terms[i].atom4] ) ;
            }
	}
    }
}

/*------------------------------------------------------------------------------
! . Deactivate terms involving QC atoms.
! . qcAtoms is the selection of both pure and boundary QC atoms.
! . Already deactivated terms are not affected.
!-----------------------------------------------------------------------------*/
void FourierDihedralContainer_DeactivateQCAtomTerms ( FourierDihedralContainer *self, Selection *qcAtoms, Selection *boundaryatoms )
{
    if ( ( self != NULL ) && ( qcAtoms != NULL ) )
    {
        auto Boolean QEXCLUDE ;
        auto Integer  i, n ;
        n = FourierDihedralContainer_UpperBound ( self ) ;
        Selection_MakeFlags ( qcAtoms, n ) ;
	for ( i = 0 ; i < self->nterms ; i++ )
	{
            if ( self->terms[i].QACTIVE )
            {
                QEXCLUDE = ( qcAtoms->flags[self->terms[i].atom1] && qcAtoms->flags[self->terms[i].atom2] &&
                             qcAtoms->flags[self->terms[i].atom3] && qcAtoms->flags[self->terms[i].atom4] ) ;
                self->terms[i].QACTIVE = ! QEXCLUDE ;
            }
	}
    }
}

/*------------------------------------------------------------------------------
! . Deallocation.
!-----------------------------------------------------------------------------*/
void FourierDihedralContainer_Deallocate ( FourierDihedralContainer **self )
{
    if ( (*self) != NULL )
    {
        free ( (*self)->terms      ) ;
        free ( (*self)->parameters ) ;
        free ( (*self) ) ;
        (*self) = NULL   ;
    }
}

/*------------------------------------------------------------------------------
! . Energy and gradients.
! . Following Becker, Berendsen and van Gunsteren, JCC 16 p527 (1995).
!-----------------------------------------------------------------------------*/
double FourierDihedralContainer_Energy ( const FourierDihedralContainer *self, const Coordinates3 *coordinates3, Coordinates3 *gradients3 )
{
    Real energy = 0.0e+00 ;
    if ( ( self != NULL ) && ( coordinates3 != NULL ) )
    {
	auto Boolean   QGRADIENTS ;
        auto Real cosnphi, cosphi, df, dotij, dotlk, mn, rkj, rkj2, sinnphi, sinphi, temp ;
        auto Real dtxi, dtyi, dtzi, dtxj, dtyj, dtzj, dtxk, dtyk, dtzk, dtxl, dtyl, dtzl, m2, mx, my, mz, n2, nx, ny, nz, sx, sy, sz,
                    xij, yij, zij, xkj, ykj, zkj, xlk, ylk, zlk ;
        auto Integer    i, j, k, l, n, p, t ;
	QGRADIENTS = ( gradients3 != NULL ) ;
	for ( n = 0 ; n < self->nterms ; n++ )
	{
	    if ( self->terms[n].QACTIVE )
	    {
                /* . Local data. */
	        i = self->terms[n].atom1 ;
	        j = self->terms[n].atom2 ;
	        k = self->terms[n].atom3 ;
	        l = self->terms[n].atom4 ;
	        t = self->terms[n].type  ;
	        /* . Coordinate displacements. */
	        Coordinates3_DifferenceRow ( coordinates3, i, j, xij, yij, zij ) ;
	        Coordinates3_DifferenceRow ( coordinates3, k, j, xkj, ykj, zkj ) ;
	        Coordinates3_DifferenceRow ( coordinates3, l, k, xlk, ylk, zlk ) ;
	        rkj2 = xkj * xkj + ykj * ykj + zkj * zkj ;
	        rkj  = sqrt ( rkj2 ) ;
                /* . m and n. */
                mx = yij * zkj - zij * ykj ;
	        my = zij * xkj - xij * zkj ;
	        mz = xij * ykj - yij * xkj ;
	        nx = ylk * zkj - zlk * ykj ;
	        ny = zlk * xkj - xlk * zkj ;
	        nz = xlk * ykj - ylk * xkj ;
                m2 = mx * mx + my * my + mz * mz ;
	        n2 = nx * nx + ny * ny + nz * nz ;
	        mn = sqrt ( m2 * n2 ) ;
                /* . Cosine and sine of the dihedral. */
                cosphi =       (  mx * nx +  my * ny +  mz * nz ) / mn ;
                sinphi = rkj * ( xij * nx + yij * ny + zij * nz ) / mn ;
                /* . Cos ( n phi ) and sin ( n phi ). */
                cosnphi = 1.0e+00 ;
                sinnphi = 0.0e+00 ;
                for ( p = 1 ; p <= self->parameters[t].period ; p++ )
	        {
	            temp    = cosnphi * cosphi - sinnphi * sinphi ;
	            sinnphi = cosnphi * sinphi + sinnphi * cosphi ;
                    cosnphi = temp ;
	        }
                /* . The energy term. */
                energy += self->parameters[t].fc * ( 1.0e+00 + cosnphi * self->parameters[t].cosphase + sinnphi * self->parameters[t].sinphase ) ;
                if ( QGRADIENTS )
                {
	            /* . The derivatives. */
	            df = self->parameters[t].fc * ( ( Real ) self->parameters[t].period ) * ( cosnphi * self->parameters[t].sinphase -
	                                                                                        sinnphi * self->parameters[t].cosphase ) ;
                    /* . i and l. */
                    dtxi =   df * rkj * mx / m2 ;
                    dtyi =   df * rkj * my / m2 ;
                    dtzi =   df * rkj * mz / m2 ;
                    dtxl = - df * rkj * nx / n2 ;
                    dtyl = - df * rkj * ny / n2 ;
                    dtzl = - df * rkj * nz / n2 ;
                    /* . j and k. */
                    dotij = xij * xkj + yij * ykj + zij * zkj ;
                    dotlk = xlk * xkj + ylk * ykj + zlk * zkj ;
	            sx    = ( dotij * dtxi + dotlk * dtxl ) / rkj2 ;
	            sy    = ( dotij * dtyi + dotlk * dtyl ) / rkj2 ;
	            sz    = ( dotij * dtzi + dotlk * dtzl ) / rkj2 ;
	            dtxj  =   sx - dtxi ;
	            dtyj  =   sy - dtyi ;
	            dtzj  =   sz - dtzi ;
	            dtxk  = - sx - dtxl ;
	            dtyk  = - sy - dtyl ;
	            dtzk  = - sz - dtzl ;
                    /* . Add in the contributions. */
	            Coordinates3_IncrementRow ( gradients3, i, dtxi, dtyi, dtzi ) ;
	            Coordinates3_IncrementRow ( gradients3, j, dtxj, dtyj, dtzj ) ;
	            Coordinates3_IncrementRow ( gradients3, k, dtxk, dtyk, dtzk ) ;
	            Coordinates3_IncrementRow ( gradients3, l, dtxl, dtyl, dtzl ) ;
        	}
	    }
	}
    }
    return energy ;
}

/*------------------------------------------------------------------------------
! . Fill the cos and sin phases of the parameter array.
!-----------------------------------------------------------------------------*/
void FourierDihedralContainer_FillCosSinPhases ( FourierDihedralContainer *self )
{
    if ( self != NULL )
    {
        auto Integer i ;
        for ( i = 0; i < self->nparameters ; i++ )
        {
            self->parameters[i].cosphase = cos ( self->parameters[i].phase ) ;
            self->parameters[i].sinphase = sin ( self->parameters[i].phase ) ;
        }
    }
}

/*------------------------------------------------------------------------------
! . Merging.
!-----------------------------------------------------------------------------*/
FourierDihedralContainer *FourierDihedralContainer_Merge ( const FourierDihedralContainer *self, const FourierDihedralContainer *other, const Integer atomincrement )
{
    FourierDihedralContainer *new = NULL ;
    if ( ( self != NULL ) && ( other != NULL ) )
    {
        auto Integer i ;
        new = FourierDihedralContainer_Allocate ( self->nterms + other->nterms, self->nparameters + other->nparameters ) ;
        for ( i = 0 ; i < self->nterms ; i++ )
        {
            new->terms[i].QACTIVE = self->terms[i].QACTIVE ;
            new->terms[i].atom1   = self->terms[i].atom1   ;
            new->terms[i].atom2   = self->terms[i].atom2   ;
            new->terms[i].atom3   = self->terms[i].atom3   ;
            new->terms[i].atom4   = self->terms[i].atom4   ;
            new->terms[i].type    = self->terms[i].type    ;
        }
        for ( i = 0 ; i < other->nterms ; i++ )
        {
            new->terms[i+self->nterms].QACTIVE = other->terms[i].QACTIVE ;
            new->terms[i+self->nterms].atom1   = other->terms[i].atom1 + atomincrement     ;
            new->terms[i+self->nterms].atom2   = other->terms[i].atom2 + atomincrement     ;
            new->terms[i+self->nterms].atom3   = other->terms[i].atom3 + atomincrement     ;
            new->terms[i+self->nterms].atom4   = other->terms[i].atom4 + atomincrement     ;
            new->terms[i+self->nterms].type    = other->terms[i].type  + self->nparameters ;
        }
        for ( i = 0 ; i < self->nparameters ; i++ )
        {
            new->parameters[i].fc       = self->parameters[i].fc       ;
            new->parameters[i].period   = self->parameters[i].period   ;
            new->parameters[i].phase    = self->parameters[i].phase    ;
            new->parameters[i].cosphase = self->parameters[i].cosphase ;
            new->parameters[i].sinphase = self->parameters[i].sinphase ;
        }
        for ( i = 0 ; i < other->nparameters ; i++ )
        {
            new->parameters[i+self->nparameters].fc       = other->parameters[i].fc       ;
            new->parameters[i+self->nparameters].period   = other->parameters[i].period   ;
            new->parameters[i+self->nparameters].phase    = other->parameters[i].phase    ;
            new->parameters[i+self->nparameters].cosphase = other->parameters[i].cosphase ;
            new->parameters[i+self->nparameters].sinphase = other->parameters[i].sinphase ;
        }
        new->QSORTED = ( self->QSORTED && other->QSORTED ) ;
    }
    return new ;
}

/*------------------------------------------------------------------------------
! . Return the number of inactive terms.
!-----------------------------------------------------------------------------*/
int FourierDihedralContainer_NumberOfInactiveTerms ( const FourierDihedralContainer *self )
{
    Integer n = 0 ;
    if ( self != NULL )
    {
        auto Integer i ;
	for ( i = 0 ; i < self->nterms ; i++ ) if ( ! self->terms[i].QACTIVE ) n++ ;
    }
    return n ;
}

/*------------------------------------------------------------------------------
! . Pruning.
! . Only terms are pruned.
!-----------------------------------------------------------------------------*/
FourierDihedralContainer *FourierDihedralContainer_Prune ( FourierDihedralContainer *self, Selection *selection )
{
    FourierDihedralContainer *new = NULL ;
    if ( ( self != NULL ) && ( selection != NULL ) )
    {
        auto Boolean *flags ;
        auto Integer   i, n  ;
        n = FourierDihedralContainer_UpperBound ( self ) ;
        Selection_MakeFlags     ( selection, n ) ;
        Selection_MakePositions ( selection, n ) ;
        flags = Memory_Allocate_Array_Boolean ( self->nterms ) ;
	for ( i = 0, n = 0 ; i < self->nterms ; i++ )
	{
            flags[i] = ( selection->flags[self->terms[i].atom1] && selection->flags[self->terms[i].atom2] &&
                         selection->flags[self->terms[i].atom3] && selection->flags[self->terms[i].atom4] ) ;
            if ( flags[i] ) n++ ;
	}
	if ( n > 0 )
	{
            new = FourierDihedralContainer_Allocate ( n, self->nparameters ) ;
            for ( i = 0 ; i < self->nparameters ; i++ )
            {
                new->parameters[i].fc       = self->parameters[i].fc       ;
                new->parameters[i].period   = self->parameters[i].period   ;
                new->parameters[i].phase    = self->parameters[i].phase    ;
                new->parameters[i].cosphase = self->parameters[i].cosphase ;
                new->parameters[i].sinphase = self->parameters[i].sinphase ;
            }
            for ( i = 0, n = 0 ; i < self->nterms ; i++ )
            {
                if ( flags[i] )
                {
        	    new->terms[n].QACTIVE =                      self->terms[i].QACTIVE ;
        	    new->terms[n].atom1   = selection->positions[self->terms[i].atom1]  ;
        	    new->terms[n].atom2   = selection->positions[self->terms[i].atom2]  ;
        	    new->terms[n].atom3   = selection->positions[self->terms[i].atom3]  ;
        	    new->terms[n].atom4   = selection->positions[self->terms[i].atom4]  ;
        	    new->terms[n].type    =                      self->terms[i].type    ;
        	    n++ ;
                }
            }
            new->QSORTED = self->QSORTED ;
	}
	Memory_Deallocate ( flags ) ;
    }
    return new ;
}

/*------------------------------------------------------------------------------
! . Sorting.
! . Within a fourierdihedral, atom2 > atom3.
! . Within the array, ordering is done with increased values of atom2 and then
! . atom3 and then atom1 and then atom4.
! . Duplicates are not removed.
!-----------------------------------------------------------------------------*/
void FourierDihedralContainer_Sort ( FourierDihedralContainer *self )
{
    if ( ( self != NULL ) && ( ! self->QSORTED ) )
    {
        auto Integer atom1, atom2, atom3, atom4, i ;
        /* . Order atom2 and atom3 within each term. */
        for ( i = 0 ; i < self->nterms ; i++ )
        {
            atom1 = self->terms[i].atom1 ;
            atom2 = self->terms[i].atom2 ;
            atom3 = self->terms[i].atom3 ;
            atom4 = self->terms[i].atom4 ;
            if ( atom3 > atom2 )
            {
                self->terms[i].atom1 = atom4 ;
                self->terms[i].atom2 = atom3 ;
                self->terms[i].atom3 = atom2 ;
                self->terms[i].atom4 = atom1 ;
            }
        }
        /* . Order the terms within the container. */
        qsort ( ( void * ) self->terms, ( size_t ) self->nterms, sizeof ( FourierDihedral ), ( void * ) FourierDihedralTerm_Compare ) ;
        self->QSORTED    = True ;
    }
}

/*------------------------------------------------------------------------------
! . Return the upper bound for the container.
! . This is the value of the largest index plus one.
!-----------------------------------------------------------------------------*/
int FourierDihedralContainer_UpperBound ( FourierDihedralContainer *self )
{
    Integer upperBound = 0 ;
    if ( ( self != NULL ) && ( self->nterms > 0 ) )
    {
        FourierDihedralContainer_Sort ( self ) ;
        upperBound  = Maximum ( self->terms[self->nterms-1].atom1, self->terms[self->nterms-1].atom2 ) ;
        upperBound  = Maximum ( upperBound, self->terms[self->nterms-1].atom4 ) ;
        upperBound += 1 ;
    }
    return upperBound ;
}

/*==============================================================================
! . Private procedures.
!============================================================================*/
static Integer FourierDihedralTerm_Compare ( const void *vterm1, const void *vterm2 )
{
    FourierDihedral *term1, *term2 ;
    Integer i ;
    term1 = ( FourierDihedral * ) vterm1 ;
    term2 = ( FourierDihedral * ) vterm2 ;
         if ( term1->atom2 < term2->atom2 ) i = -1 ;
    else if ( term1->atom2 > term2->atom2 ) i =  1 ;
    else if ( term1->atom3 < term2->atom3 ) i = -1 ;
    else if ( term1->atom3 > term2->atom3 ) i =  1 ;
    else if ( term1->atom1 < term2->atom1 ) i = -1 ;
    else if ( term1->atom1 > term2->atom1 ) i =  1 ;
    else if ( term1->atom4 < term2->atom4 ) i = -1 ;
    else if ( term1->atom4 > term2->atom4 ) i =  1 ;
    else if ( term1->type  < term2->type  ) i = -1 ;
    else if ( term1->type  > term2->type  ) i =  1 ;
    else if ( ! term1->QACTIVE && term2->QACTIVE ) i = -1 ;
    else if ( term1->QACTIVE && ! term2->QACTIVE ) i =  1 ;
    else i = 0 ;
    return i ;
}
