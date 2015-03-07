#-------------------------------------------------------------------------------
# . File      : ChainOfStatesOptimizer.py
# . Program   : pDynamo-1.9.0                           (http://www.pdynamo.org)
# . Copyright : CEA, CNRS, Martin J. Field (2007-2014)
# . License   : CeCILL French Free Software License     (http://www.cecill.info)
#-------------------------------------------------------------------------------
"""Chain-of-states path optimization."""

import math

from pCore import LBFGSMinimizer, logFile, LogFileActive, MultiDimensionalMinimizer, PrintPriority_Low

from ChainOfStatesObjectiveFunction import ChainOfStatesObjectiveFunction
from ChainOfStatesOptimizerState    import ChainOfStatesOptimizerState
from SGOFProcessPool                import SGOFProcessPoolFactory

"""
Notes:

For climbing image have only one image active and cannot use splines.
Best to have separate module? Possibly with adaptive method?

Have imageInteraction object for springs, saw or None?

MaxFlux?

Have keywords for groups of options (e.g. HEB, NEB, SAW, String, etc.)?
"""

#===================================================================================================================================
# . Class.
#===================================================================================================================================
class ChainOfStatesOptimizer ( MultiDimensionalMinimizer ):
    """A chain-of-states optimizer."""

    # . Default attributes.
    defaultAttributes = { "fixedTerminalImages"                        : True   ,
                          "forceOneSingleImageOptimization"            : False  ,
                          "forceSingleImageOptimizations"              : False  ,
                          "forceSplineRedistributionCheckPerIteration" : False  ,
                          "freezeRMSGradientTolerance"                 :   0.0  ,
                          "optimizer"                                  : None   ,
                          "poolFactory"                                : None   ,
                          "rmsGradientToleranceScale"                  :   0.25 ,
                          "splineRedistributionTolerance"              :   1.5  ,  
                          "springForceConstant"                        : 500.0  ,
                          "useSplineRedistribution"                    : False  }
    defaultAttributes.update ( MultiDimensionalMinimizer.defaultAttributes )

    # . Default attribute names.
    defaultAttributeNames = { "Fixed Terminal Images"              : "fixedTerminalImages"                        ,
                              "Freeze RMS Gradient Tolerance"      : "freezeRMSGradientTolerance"                 ,
                              "One Single Image Optimization"      : "forceOneSingleImageOptimization"            ,
                              "Optimizer"                          : "optimizer"                                  ,
                              "Optimizer Tolerance Scaling"        : "rmsGradientToleranceScale"                  ,
                              "Redistribution Check Per Iteration" : "forceSplineRedistributionCheckPerIteration" ,
                              "Single Image Optimizations"         : "forceSingleImageOptimizations"              ,
                              "Spline Redistribution Tolerance"    : "splineRedistributionTolerance"              ,
                              "Spring Force Constant"              : "springForceConstant"                        ,
                              "Use Spline Redistribution"          : "useSplineRedistribution"                    }     
    defaultAttributeNames.update ( MultiDimensionalMinimizer.defaultAttributeNames )

    # . Default optimizer and options.
    defaultOptimizer        = LBFGSMinimizer
    defaultOptimizerOptions = { "history"           : 10     ,
                                "logFrequency"      :  0     ,
                                "maximumIterations" : 10     ,
                                "maximumStep"       :  0.025 }

    # . Default pool factory and options.
    defaultPoolFactory        = SGOFProcessPoolFactory
    defaultPoolFactoryOptions = {}

    # . State class.
    stateObject = ChainOfStatesOptimizerState

    def CheckAttributes ( self ):
        """Check the options for consistency."""
        # . Set up a default optimizer.
        if self.optimizer is None:
            options = dict ( self.__class__.defaultOptimizerOptions )
            options["rmsGradientTolerance"] = self.rmsGradientTolerance * self.rmsGradientToleranceScale
            self.optimizer = self.__class__.defaultOptimizer ( **options )
        # . Check the options of a user-defined optimizer.
        else:
            self.optimizer.rmsGradientTolerance = min ( self.optimizer.rmsGradientTolerance, self.rmsGradientTolerance )
        # . Set up a pool factory.
        if self.poolFactory is None:
            self.poolFactory = self.__class__.defaultPoolFactory ( **self.__class__.defaultPoolFactoryOptions )

    def Continue ( self, state ):
        """Check to see if iterations should continue."""
        errors  = []
        notDone = []
        for ( images, optimizerState ) in state.optimizations:
            optimizerState.numberOfIterations += 1
            optimizerState.rmsGradient         = optimizerState.g.RootMeanSquare ( )
            if self.optimizer.Continue ( optimizerState ): notDone.append ( ( images, optimizerState ) )
            if optimizerState.error is not None: errors.append ( optimizerState.error )
        state.optimizations = notDone
        if len ( errors ) > 0: state.error = ( "Errors ({:d}) in image optimizations.".format ( len ( errors ) ) )
        state.rmsGradient = max ( state.path.rmsGradients )
        return super ( ChainOfStatesOptimizer, self ).Continue ( state )

    def DefineOptimizations ( self, state ):
        """Define the optimizations to perform."""
        # . Get the active images.
        if self.forceOneSingleImageOptimization:
            activeImages = [ state.path.rmsGradients.AbsoluteMaximumIndex ( ) ]
        else:
            activeImages = []
            for ( image, rmsGradient ) in enumerate ( state.path.rmsGradients ):
                if rmsGradient > self.freezeRMSGradientTolerance:
                    activeImages.append ( image )
        if len ( activeImages ) == 0: raise ValueError ( "There are no active images." ) # . Should never happen.
        # . Group together consecutive images.
        group  = [ activeImages[0] ]
        groups = []
        for image in activeImages[1:]:
            if self.forceSingleImageOptimizations or ( image != group[-1]+1 ):
                groups.append ( group )
                group = [ image ]
            else:
                group.append ( image )
        groups.append ( group )
        # . Set up the optimizations.
        toDo = []
        for group in groups:
            start =   group[ 0]       * state.numberOfImageVariables
            stop  = ( group[-1] + 1 ) * state.numberOfImageVariables
            optimizerState = self.optimizer.StateFromVariableArray ( state.path.x[start:stop], g = state.path.g[start:stop], surrogateObjectiveFunction = state.objectiveFunction )
            self.optimizer.Restart ( optimizerState )
            toDo.append ( ( group, optimizerState ) )
        # . Finish up.
        state.activeImages           = activeImages
        state.numberOfOptimizations += len ( toDo )
        state.optimizations          =       toDo

    def DetermineStep ( self, state ):
        """Perform an iteration."""
        # . Initialization.
        state.activeImages = []
        state.stepType     = ""
        # . Optimization set up.
        if len ( state.optimizations ) <= 0:
            # . Image redistribution.
            if self.useSplineRedistribution and ( not self.forceSplineRedistributionCheckPerIteration ) and ( not state.skipRedistributionCheck ):
                self.RedistributeImages ( state )
                state.skipRedistributionCheck = True
            if len ( state.activeImages ) <= 0:
                self.DefineOptimizations ( state )
                state.skipRedistributionCheck = False
        # . Do optimizations.
        if len ( state.optimizations ) > 0:
            # . Optimization steps.
            state.activeImages = []
            for ( images, optimizerState ) in state.optimizations:
                state.activeImages.extend ( images )
                self.optimizer.DetermineStep ( optimizerState )
            state.stepType = "S"
            # . Image redistribution after step.
            if self.useSplineRedistribution and self.forceSplineRedistributionCheckPerIteration:
                self.RedistributeImages ( state )
        # . Save images that have moved.
        state.path.Dump                ( state.objectiveFunction, images = state.activeImages )
        state.path.UpdateNonSplineData (                          images = state.activeImages )

    def FunctionGradients ( self, state ):
        """Evaluate the function and its gradients."""
        # . Active images.
        x = [ state.path.xI [image] for image in state.activeImages ]
        g = [ state.path.gIp[image] for image in state.activeImages ]
        f = state.pool.FunctionGradients ( x, g )
        # . Set function values.
        for ( image, v ) in zip ( state.activeImages, f ):
            state.numberOfFunctionCalls += 1
            state.path.functionValues[image] = v
        # . Set gradients.
        for image in state.activeImages:
            self.ImageGradient ( state, image )
        # . Semi-active images.
        # . Maybe this could be better handled by only determining semiActiveImages when activeImages changes.
        for image in state.SemiActiveImages ( ):
            self.ImageGradient ( state, image )

    def ImageGradient ( self, state, image ):
        """Calculate the gradient on an image."""
        # . Modified by Ramon Crehuet (22/04/2014) for fixed terminal images.
        g = state.path.gI[image]
        # . Terminal images.
        if ( image == 0 ) or ( image == state.numberOfImages - 1 ):
            if self.fixedTerminalImages: g.Set ( 0.0 )
            else: state.path.gIp[image].CopyTo ( g )
        # . Interior images.
        else:
            # . Calculate the normalized tangent to the image with linear constraints removed.
            t = state.tangent
            state.path.Tangent ( image, state.objectiveFunction, t ) # . Require method option.
            # . Calculate the projected function gradient.
            state.path.gIp[image].CopyTo ( g )
            a = g.Dot ( t )
            g.AddScaledArray ( -a, t )
            # . Calculate the spring forces using the method of Henkelman and Jonsson.
            if self.springForceConstant > 0.0:
                a = self.springForceConstant * ( state.path.distances1[image] - state.path.distances1[image-1] )
                g.AddScaledArray ( -a, t )
        # . Set the RMS gradient for the image.
        state.path.rmsGradients[image] = g.RootMeanSquare ( )
 
    def Initialize ( self, state ):
        """Initialization before iterating."""
        state.optimizations = []
        state.pool          = self.poolFactory.PoolFromObjectiveFunction ( state.objectiveFunction )
        state.stepType      = "I"
        if self.useSplineRedistribution: self.RedistributeImages ( state )
        state.activeImages  = range ( state.numberOfImages )
        state.path.UpdateNonSplineData ( images = state.activeImages )
        self.FunctionGradients   ( state )
        self.DefineOptimizations ( state )

    def Label ( self ): return "Chain-Of-States Optimizer"

    def LogIteration ( self, state ):
        """Log an iteration."""
        if ( state.table is not None ) and ( state.numberOfIterations % self.logFrequency == 0 ):
            state.table.Entry ( "{:d}".format ( state.numberOfIterations    ) )
            state.table.Entry ( state.stepType                )
            state.table.Entry ( "{:d}"    .format ( len ( state.activeImages )      ) )
            state.table.Entry ( "{:d}"    .format ( state.numberOfFunctionCalls     ) )
            state.table.Entry ( "{:d}"    .format ( state.numberOfOptimizations     ) )
            state.table.Entry ( "{:20.8f}".format ( max ( state.path.rmsGradients ) ) )
            state.table.Entry ( "{:20.3f}".format ( sum ( state.path.distances1   ) ) )
            state.table.Entry ( "{:20.1f}".format ( min ( state.path.angles[1:-1] ) ) )

    def LogStart ( self, state, log = logFile ):
        """Start logging."""
        if ( self.logFrequency > 0 ) and LogFileActive ( log, pushPriority = PrintPriority_Low ):
            state.log   = log
            state.table = log.GetTable ( columns = [ 6, 6, 18, 20, 20, 20, 20, 20 ] )
            state.table.Start ( )
            state.table.Heading ( "Iteration", columnSpan = 2 )
            state.table.Heading ( "Active Images"     )
            state.table.Heading ( "Function Calls"    )
            state.table.Heading ( "Optimizations"     )
            state.table.Heading ( "Max. RMS Gradient" )
            state.table.Heading ( "Path Length"       )
            state.table.Heading ( "Min. Angle"        )

    def LogStop ( self, state ):
        """Stop logging."""
        # . Update path data - probably should not be here.
        state.path.UpdateNonSplineData ( )
        if state.path.imageSpline is not None: state.path.UpdateSplineData ( )
        # . Output.
        if state.log is not None:
            state.table.Stop ( )
            if state.statusMessage is not None: state.log.Paragraph ( state.statusMessage )
            table = state.log.GetTable ( columns = [ 30, 20 ] )
            table.Start ( )
            table.Title ( self.Label ( ) + " Statistics" )
	    table.Entry ( "Iterations"                 , alignment = "left" ) ; table.Entry ( "{:d}"     .format ( state.numberOfIterations        ) )
	    table.Entry ( "Function Calls"             , alignment = "left" ) ; table.Entry ( "{:d}"     .format ( state.numberOfFunctionCalls     ) )
            table.Entry ( "Maximum Image RMS Gradient" , alignment = "left" ) ; table.Entry ( "{:20.10g}".format ( max ( state.path.rmsGradients ) ) )
	    table.Entry ( "Optimizations"              , alignment = "left" ) ; table.Entry ( "{:d}"     .format ( state.numberOfOptimizations     ) )
	    table.Entry ( "Redistributions"            , alignment = "left" ) ; table.Entry ( "{:d}"     .format ( state.numberOfRedistributions   ) )
	    table.Stop ( )
            state.log.PriorityPop ( )
            state.path.Summary ( log = state.log )

    def RedistributeImages ( self, state ):
        """Redistribute the images along the path if necessary."""
        state.path.UpdateSplineData ( )
        if state.path.Irregularity ( ) > self.splineRedistributionTolerance:
            state.path.RedistributeImages ( )
            if self.fixedTerminalImages: state.activeImages = range ( 1, state.numberOfImages - 1 )
            else:                        state.activeImages = range (    state.numberOfImages     )
            state.numberOfRedistributions += 1
            state.stepType                += "R"

    def StateFromObjectiveFunction ( self, objectiveFunction ):
        """Set up the state."""
        return self.__class__.stateObject.FromObjectiveFunction ( objectiveFunction, fixedTerminalImages = self.fixedTerminalImages )

    def Summary ( self, log = logFile ):
        """Summary."""
        super ( ChainOfStatesOptimizer, self ).Summary ( log = log, pageWidth = 120, valueWidth = 20 )
        self.optimizer.Summary   ( log = log )
        self.poolFactory.Summary ( log = log )

#===================================================================================================================================
# . Function.
#===================================================================================================================================
# . Helper function to perform optimization.
# . Keyword arguments are those of ChainOfStatesOptimizer.defaultAttributes along with "log".
def ChainOfStatesOptimizePath_SystemGeometry ( system, imageTrajectory, **keywordArguments ):
    """Chain-of-states path optimization."""
    # . Get the log file.
    log = keywordArguments.pop ( "log", logFile )
    # . Create an objective function.
    of = ChainOfStatesObjectiveFunction.FromSystem ( system )
    of.InitializeImages ( imageTrajectory )
    of.RemoveRotationTranslation ( reference = system.coordinates3 )
    # . Optimization.
    optimizer = ChainOfStatesOptimizer ( **keywordArguments )
    optimizer.Summary ( log = log )  
    return optimizer.Iterate ( of, log = log )

#===================================================================================================================================
# . Testing.
#===================================================================================================================================
if __name__ == "__main__" :
    pass

