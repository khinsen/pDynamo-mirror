#-------------------------------------------------------------------------------
# . File      : MultiDimensionalMinimizer.py
# . Program   : pDynamo-1.9.0                           (http://www.pdynamo.org)
# . Copyright : CEA, CNRS, Martin J. Field (2007-2014)
# . License   : CeCILL French Free Software License     (http://www.cecill.info)
#-------------------------------------------------------------------------------
"""Base classes for multidimensional minimization algorithms."""

from LogFileWriter             import logFile, LogFileActive, PrintPriority_Low
from ObjectiveFunctionIterator import ObjectiveFunctionIterator, ObjectiveFunctionIteratorState
from Real1DArray               import Real1DArray

"""
Have saveBestPoint option?
After FunctionGradients have:
if self.saveBestPoint:
    state.lastPointIsBest = ( state.f <= state.fBest )
    if state.lastPointIsBest:
        state.fBest = state.f
        state.x.CopyTo ( state.xBest )

In Finalizer have:
if self.saveBestPoint and ( not state.lastPointIsBest ):
    state.f = state.fBest
    state.xBest.CopyTo ( state.x )
    self.FunctionGradients ( )
"""

#===================================================================================================================================
# . Class.
#===================================================================================================================================
class MultiDimensionalMinimizerState ( ObjectiveFunctionIteratorState ):
    """Base class for multidimensional minimization algorithms."""

    # . Default attributes.
    defaultAttributes = { "alpha"                 : 1.0   , # . The step scaling factor.
                          "d"                     : None  , # . The step vector.
                          "g"                     : None  ,
                          "isConverged"           : False ,
                          "numberOfFunctionCalls" : 0     ,
                          "rmsGradient"           : None  ,
                          "stepType"              : ""    }
    defaultAttributes.update ( ObjectiveFunctionIteratorState.defaultAttributes )

    def ExtractSurrogateData ( self, surrogate ):
        """Extract additional data from a surrogate objective function."""
        pass

    def Finalize ( self ):
        """Finalization."""
        report = { "Converged"      : self.isConverged           ,
                   "Function Calls" : self.numberOfFunctionCalls ,
                   "RMS Gradient"   : self.rmsGradient           }
        report.update ( super ( MultiDimensionalMinimizerState, self ).Finalize ( ) )
        return report

    @classmethod
    def FromVariableArray ( selfClass, x, d = None, g = None, surrogateObjectiveFunction = None ):
        """Constructor given a variable array."""
        self = selfClass ( )
        self.numberOfVariables = len ( x )
        self.d = d
        self.g = g
        self.x = x
        self.SetUp ( )
        self.ExtractSurrogateData ( surrogateObjectiveFunction )
        return self

    def SetUp ( self ):
       """Set up the state."""
       n = self.numberOfVariables
       if self.d is None: self.d = Real1DArray.WithExtent ( n ) ; self.d.Set ( 0.0 )
       if self.g is None: self.g = Real1DArray.WithExtent ( n ) ; self.g.Set ( 0.0 )

#===================================================================================================================================
# . Class.
#===================================================================================================================================
class MultiDimensionalMinimizer ( ObjectiveFunctionIterator ):
    """Base class for multidimensional minimization algorithms."""

    # . Default attributes.
    defaultAttributes = { "rmsGradientTolerance" : 1.0e-3 }
    defaultAttributes.update ( ObjectiveFunctionIterator.defaultAttributes )

    # . Default attribute names.
    defaultAttributeNames = { "RMS Gradient Tolerance" : "rmsGradientTolerance" }
    defaultAttributeNames.update ( ObjectiveFunctionIterator.defaultAttributeNames )

    # . State class.
    stateObject = MultiDimensionalMinimizerState

    def Continue ( self, state ):
        """Check to see if iterations should continue."""
        state.isConverged = ( state.rmsGradient <= self.rmsGradientTolerance )
        if   state.isConverged:                                  state.statusMessage = "Minimization converged."
        elif state.numberOfIterations >= self.maximumIterations: state.statusMessage = "Too many iterations."
        elif state.error is not None:                            state.statusMessage = "Minimization error: " + state.error
        else: state.statusMessage = None
        return ( state.statusMessage is None )

    def DetermineStep ( state ):
        """Determine the step."""
        state.d.Set ( 0.0 )
        state.x.AddScaledArray ( state.alpha, state.d )
        state.stepType = "N"

    def FunctionGradients ( self, state ):
        """Evaluate the function and its gradients."""
        state.f = state.objectiveFunction.FunctionGradients ( state.x, state.g )
        state.rmsGradient = state.g.RootMeanSquare ( )
        state.numberOfFunctionCalls += 1

    def Initialize ( self, state ):
        """Initialization before iteration."""
        state.stepType = "I"
        try:
            self.FunctionGradients ( state )
        except Exception as error:
            state.error = error[0]

    def Iteration ( self, state ):
        """Perform an iteration."""
        try:
            self.DetermineStep     ( state )
            self.FunctionGradients ( state )
        except Exception as error:
            state.error = error[0]
            import traceback, sys
            traceback.print_exc(file=sys.stdout)
        state.numberOfIterations += 1

    def Label ( self ): return "Multi-Dimensional Minimizer"

    def LogIteration ( self, state ):
        """Log an iteration."""
        state.objectiveFunction.LogIteration ( state.numberOfIterations )
        if ( state.table is not None ) and ( state.numberOfIterations % self.logFrequency == 0 ):
            state.table.Entry ( "{:d}".format ( state.numberOfIterations ) )
            state.table.Entry ( state.stepType )
            state.table.Entry ( "{:20.8f}".format ( state.f                                   ) )
            state.table.Entry ( "{:20.8f}".format ( state.rmsGradient                         ) )
            state.table.Entry ( "{:20.8f}".format ( state.g.AbsoluteMaximum               ( ) ) )
            state.table.Entry ( "{:20.8f}".format ( state.alpha * state.d.RootMeanSquare  ( ) ) )
            state.table.Entry ( "{:20.8f}".format ( state.alpha * state.d.AbsoluteMaximum ( ) ) )

    def LogStart ( self, state, log = logFile ):
        """Start logging."""
        state.objectiveFunction.LogStart ( )
        if ( self.logFrequency > 0 ) and LogFileActive ( log, pushPriority = PrintPriority_Low ):
            state.log   = log
            state.table = log.GetTable ( columns = [ 6, 6, 20, 20, 20, 20, 20 ] )
            state.table.Start ( )
            state.table.Heading ( "Iteration", columnSpan = 2 )
            state.table.Heading ( "Function"     )
            state.table.Heading ( "RMS Gradient" )
            state.table.Heading ( "Max. |Grad.|" )
            state.table.Heading ( "RMS Disp."    )
            state.table.Heading ( "Max. |Disp.|" )

    def LogStop ( self, state ):
        """Stop logging."""
        state.objectiveFunction.LogStop ( )
        if state.log is not None:
            state.table.Stop ( )
            if state.statusMessage is not None: state.log.Paragraph ( state.statusMessage )
            summary = state.log.GetSummary ( )
            summary.Start ( self.Label ( ) + " Statistics" )
	    summary.Entry ( "Iterations",     "{:d}".format ( state.numberOfIterations    ) )
	    summary.Entry ( "Function Calls", "{:d}".format ( state.numberOfFunctionCalls ) )
	    summary.Stop ( )
            state.log.PriorityPop ( )

    def StateFromVariableArray ( self, x, d = None, g = None, surrogateObjectiveFunction = None ):
        """Set up the state."""
        return self.__class__.stateObject.FromVariableArray ( x, d = d, g = g, surrogateObjectiveFunction = surrogateObjectiveFunction )

#===================================================================================================================================
# . Testing.
#===================================================================================================================================
if __name__ == "__main__" :
    pass
