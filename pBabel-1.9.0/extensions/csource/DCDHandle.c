/*==================================================================================================================================
! . DCD trajectory file handling.
! . Heavily modified from the VMD DCD plugin.
!=================================================================================================================================*/

/* . Includes. */
# include "fastio.h"

# include "DCDHandle.h"
# include "MemoryBlock.h"

/*----------------------------------------------------------------------------------------------------------------------------------
! . Allocation.
!---------------------------------------------------------------------------------------------------------------------------------*/
DCDHandle *DCDHandle_Allocate ( void )
{
    DCDHandle *self = NULL ;
    Memory_AllocateObject ( self, DCDHandle ) ;
    if ( self != NULL )
    {
        self->has4Dimensions      = False ;
        self->hasCharges          = False ;
        self->hasUnitCell         = False ;
        self->isXPLOR             = False ;
        self->reverseEndian       = False ;
        self->useVelocityHeader   = False ;
/*        self->fileDescriptor      = NULL ; */ /* ???? */
        self->currentFrame        = 0     ;
        self->fileSize            = 0     ;
        self->firstFramePosition  = 0     ;
        self->firstFrameSize      = 0     ;
        self->frameSize           = 0     ;
        self->numberOfAtomIndices = 0     ;
        self->numberOfAtoms       = 0     ;
        self->numberOfFixedAtoms  = 0     ;
        self->numberOfFrames      = 0     ;
        self->recordMarkerScale   = 0     ;
        self->saveFrequency       = 1     ;
        self->startingFrame       = 0     ;
        self->timeStep            = 0.001 ;
/*        self->unitCell            = { 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 } ; */
        self->q                   = NULL  ;
        self->w                   = NULL  ;
        self->x                   = NULL  ;
        self->y                   = NULL  ;
        self->z                   = NULL  ;
        self->atomIndices         = NULL  ;
        self->data3               = NULL  ;
        self->symmetryParameters  = NULL  ;
    }
    return self ;
}

/*----------------------------------------------------------------------------------------------------------------------------------
! . Allocate Q and W if necessary.
!---------------------------------------------------------------------------------------------------------------------------------*/
DCDStatus DCDHandle_AllocateQW ( DCDHandle *self )
{
    DCDStatus status = DCDStatus_Normal ;
    if ( self != NULL )
    {
        Memory_DeallocateArray ( self->q ) ;
        Memory_DeallocateArray ( self->w ) ;
        if ( self->numberOfAtoms > 0 )
        {
            auto Boolean isOK = True ;
            if ( self->has4Dimensions )
            {
                Memory_AllocateArray ( self->w, self->numberOfAtoms, Float32 ) ;
                isOK = isOK && ( self->w != NULL ) ;
            }
            if ( self->hasCharges )
            {
                Memory_AllocateArray ( self->q, self->numberOfAtoms, Float32 ) ;
                isOK = isOK && ( self->q != NULL ) ;
            }
            if ( ! isOK ) { status = DCDStatus_MemoryAllocationFailure ; }
        }
    }
    return status ;
}

/*----------------------------------------------------------------------------------------------------------------------------------
! . Check the number of atoms.
!---------------------------------------------------------------------------------------------------------------------------------*/
DCDStatus DCDHandle_CheckNumberOfAtoms ( DCDHandle *self, const Integer numberOfAtoms )
{
    DCDStatus status = DCDStatus_Normal ;
    if ( self != NULL )
    {
        if ( self->numberOfAtoms != numberOfAtoms ) status = DCDStatus_AtomNumberMismatch ;
    }
    return status ;
}

/*----------------------------------------------------------------------------------------------------------------------------------
! . Number of frames.
!---------------------------------------------------------------------------------------------------------------------------------*/
Integer DCDHandle_CurrentFrame ( DCDHandle *self )
{
    Integer n = 0 ;
    if ( self != NULL ) { n = self->currentFrame ; }
    return n ;
}

/*----------------------------------------------------------------------------------------------------------------------------------
! . Deallocation.
!---------------------------------------------------------------------------------------------------------------------------------*/
void DCDHandle_Deallocate ( DCDHandle **self )
{
    if ( ( self != NULL ) && ( (*self) != NULL ) )
    {
        Memory_DeallocateArray  ( (*self)->atomIndices ) ;
        Memory_DeallocateArray  ( (*self)->q ) ;
        Memory_DeallocateArray  ( (*self)->w ) ;
        Memory_DeallocateArray  ( (*self)->x ) ;
        Memory_DeallocateArray  ( (*self)->y ) ;
        Memory_DeallocateArray  ( (*self)->z ) ;
        Memory_DeallocateObject ( (*self) ) ;
    }
}

/*----------------------------------------------------------------------------------------------------------------------------------
! . Number of frames.
!---------------------------------------------------------------------------------------------------------------------------------*/
Integer DCDHandle_NumberOfFrames ( DCDHandle *self )
{
    Integer n = 0 ;
    if ( self != NULL ) { n = self->numberOfFrames ; }
    return n ;
}

/*----------------------------------------------------------------------------------------------------------------------------------
! . Set atom indices.
!---------------------------------------------------------------------------------------------------------------------------------*/
DCDStatus DCDHandle_SetAtomIndices ( DCDHandle *self, Selection *selection )
{
    DCDStatus status = DCDStatus_Normal ;
    if ( self != NULL )
    {
        auto Integer extent = Selection_Size ( selection ) ;
        Memory_DeallocateArray ( self->atomIndices ) ;
        self->numberOfAtomIndices = 0 ;
        if ( extent > 0 )
        {
            Memory_AllocateArray ( self->atomIndices, extent, Integer32 ) ;
            if ( self->atomIndices == NULL ) { status = DCDStatus_MemoryAllocationFailure ; }
            else
            {
                auto Integer i ;
                for ( i = 0 ; i < extent ; i++ ) self->atomIndices[i] = ( selection->indices[i] + 1 ) ;
                self->numberOfAtomIndices = extent ;
            }
        }
    }
    return status ;
}

/*----------------------------------------------------------------------------------------------------------------------------------
! . Set the XYZ data.
!---------------------------------------------------------------------------------------------------------------------------------*/
DCDStatus DCDHandle_SetData3 ( DCDHandle *self, Coordinates3 *data3 )
{
    DCDStatus status = DCDStatus_Normal ;
    if ( self != NULL )
    {
        auto Integer extent = Coordinates3_Rows ( data3 ) ;
        Memory_DeallocateArray ( self->x ) ;
        Memory_DeallocateArray ( self->y ) ;
        Memory_DeallocateArray ( self->z ) ;
        self->numberOfAtoms = 0 ;
        if ( extent > 0 )
        {
            Memory_AllocateArray ( self->x, extent, Float32 ) ;
            Memory_AllocateArray ( self->y, extent, Float32 ) ;
            Memory_AllocateArray ( self->z, extent, Float32 ) ;
            if ( ( self->x == NULL ) || ( self->y == NULL ) || ( self->z == NULL ) ) { status = DCDStatus_MemoryAllocationFailure ; }
            else { self->data3 = data3 ; self->numberOfAtoms = extent ; }
        }
        else { status = DCDStatus_InvalidDataObject ; }
    }
    return status ;
}

/*----------------------------------------------------------------------------------------------------------------------------------
! . Set symmetry parameters.
!---------------------------------------------------------------------------------------------------------------------------------*/
DCDStatus DCDHandle_SetSymmetryParameters ( DCDHandle  *self, SymmetryParameters *symmetryParameters )
{
    DCDStatus status = DCDStatus_Normal ;
    if ( self != NULL )
    {
        self->hasUnitCell        = False ;
        self->symmetryParameters = NULL  ;
        if ( symmetryParameters != NULL )
        {
            self->hasUnitCell        = True  ;
            self->isXPLOR            = False ;
            self->symmetryParameters = symmetryParameters ;
        }
    }
    return status ;
}
