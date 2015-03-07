/*------------------------------------------------------------------------------
! . File      : PairListGenerator.h
! . Program   : pDynamo-1.9.0                           (http://www.pdynamo.org)
! . Copyright : CEA, CNRS, Martin J. Field (2007-2014)
! . License   : CeCILL French Free Software License     (http://www.cecill.info)
!-----------------------------------------------------------------------------*/
# ifndef _PAIRLISTGENERATOR
# define _PAIRLISTGENERATOR

# include "Boolean.h"
# include "Coordinates3.h"
# include "Integer.h"
# include "PairList.h"
# include "Real.h"
# include "Real1DArray.h"
# include "RegularGrid.h"
# include "RegularGridOccupancy.h"
# include "Selection.h"
# include "Status.h"

/*----------------------------------------------------------------------------------------------------------------------------------
! . Definitions.
!---------------------------------------------------------------------------------------------------------------------------------*/
/* . The pairlist generator type. */
typedef struct {
    Boolean sortIndices          ;
    Boolean useGridByCell        ;
    Integer minimumCellExtent    ;
    Integer minimumPoints        ;
    Real    cellSize             ;
    Real    cutoff               ;
    Real    cutoffCellSizeFactor ;
    Real    minimumCellSize      ;
    Real    minimumExtentFactor  ;
} PairListGenerator ;

/*----------------------------------------------------------------------------------------------------------------------------------
! . Procedure declarations.
!---------------------------------------------------------------------------------------------------------------------------------*/
/* . General procedures. */
extern PairListGenerator *PairListGenerator_Allocate        ( void ) ;
extern PairListGenerator *PairListGenerator_Clone           ( const PairListGenerator  *self ) ;
extern void               PairListGenerator_Deallocate      (       PairListGenerator **self ) ;
extern Boolean            PairListGenerator_DetermineMethod ( const PairListGenerator  *self, const Coordinates3 *coordinates3, const Selection *andSelection ) ;

/* . Generation procedures. */
extern PairList *PairListGenerator_CrossPairListFromDoubleCoordinates3 ( const PairListGenerator *self          ,
                                                                         const Coordinates3      *coordinates31 ,
                                                                         const Coordinates3      *coordinates32 ,
                                                                         const Real1DArray       *radii1        ,
                                                                         const Real1DArray       *radii2        ,
                                                                         Selection               *andSelection1 ,
                                                                         Selection               *andSelection2 ,
                                                                         Selection               *orSelection1  ,
                                                                         Selection               *orSelection2  ,
                                                                         PairList                *exclusions    ,
                                                                         RegularGrid             *grid1         ,
                                                                         RegularGridOccupancy    *occupancy1    ,
                                                                         Status                  *status        ) ;
extern PairList *PairListGenerator_CrossPairListFromSingleCoordinates3 ( const PairListGenerator *self          ,
                                                                         const Coordinates3      *coordinates3  ,
                                                                         const Real1DArray       *radii         ,
                                                                         Selection               *andSelection1 ,
                                                                         Selection               *andSelection2 ,
                                                                         Selection               *orSelection   ,
                                                                         PairList                *exclusions    ,
                                                                         const Boolean            excludeSelf   ,
                                                                         RegularGrid             *grid1         ,
                                                                         RegularGridOccupancy    *occupancy1    ,
                                                                         Status                  *status        ) ;
extern PairList *PairListGenerator_SelfPairListFromCoordinates3        ( const PairListGenerator *self          ,
                                                                         const Coordinates3      *coordinates3  ,
                                                                         const Real1DArray       *radii         ,
                                                                         Selection               *andSelection  ,
                                                                         Selection               *orSelection   ,
                                                                         PairList                *exclusions    ,
                                                                         RegularGrid             *grid          ,
                                                                         RegularGridOccupancy    *occupancy     ,
                                                                         Status                  *status        ) ;
# endif
