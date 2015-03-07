#-------------------------------------------------------------------------------
# . File      : ChainOfStatesOptimizerState.py
# . Program   : pDynamo-1.9.0                           (http://www.pdynamo.org)
# . Copyright : CEA, CNRS, Martin J. Field (2007-2014)
# . License   : CeCILL French Free Software License     (http://www.cecill.info)
#-------------------------------------------------------------------------------
"""The state for a chain-of-states path optimization."""

from pCore import Real1DArray

from ChainOfStatesObjectiveFunction import ChainOfStatesObjectiveFunction
from ChainOfStatesPath              import ChainOfStatesPath
#from SGOFProcess                    import SGOFProcessPool

#===================================================================================================================================
# . Class.
#===================================================================================================================================
class ChainOfStatesOptimizerState ( object ):
    """The state for the chain-of-states exec."""

    # . Default attributes.
    defaultAttributes = { "activeImages"            : None  ,
                          "error"                   : None  ,
                          "isConverged"             : False ,
                          "log"                     : None  ,
                          "numberOfFunctionCalls"   : 0     ,
                          "numberOfImages"          : None  ,
                          "numberOfIterations"      : 0     ,
                          "numberOfImageVariables"  : 0     ,
                          "numberOfOptimizations"   : 0     ,
                          "numberOfRedistributions" : 0     ,
                          "numberOfVariables"       : 0     ,
                          "objectiveFunction"       : None  ,
                          "optimizations"           : None  ,
                          "path"                    : None  ,
                          "pool"                    : None  ,
                          "rmsGradient"             : None  ,
                          "skipRedistributionCheck" : False ,
                          "statusMessage"           : None  ,
                          "stepType"                : None  ,
                          "table"                   : None  ,
                          "tangent"                 : None  }

    # . Objective function class.
    objectiveFunctionClass = ChainOfStatesObjectiveFunction

    def __init__ ( self ):
        """Constructor."""
        for ( key, value ) in self.__class__.defaultAttributes.iteritems ( ): setattr ( self, key, value )

    def Finalize ( self ):
        """Clear up."""
        # . Create the report.
        report = {}
        report["Converged"                 ] = self.isConverged           
        report["Function Calls"            ] = self.numberOfFunctionCalls 
        report["Iterations"                ] = self.numberOfIterations    
        report["Maximum Image RMS Gradient"] = max ( self.path.rmsGradients )
        report["Optimizations"             ] = self.numberOfOptimizations
        report["Path"                      ] = self.path
        if self.error is not None: report["Error"] = self.error
        # . Finalize various member objects.
        for label in ( "objectiveFunction", "path", "pool" ): # optimizations?
            member = getattr ( self, label, None )
            if ( member is not None ) and hasattr ( member, "Finalize" ): member.Finalize ( )
        # . Finish up.
        return report

    @classmethod
    def FromObjectiveFunction ( selfClass, objectiveFunction, fixedTerminalImages = True ):
        """Constructor given an objective function."""
        # . Create the object.
        self = selfClass ( )
        # . Set the objective function and associated data.
        if not isinstance ( objectiveFunction, self.__class__.objectiveFunctionClass ): raise TypeError ( "Invalid objective function." )
        self.numberOfImages         = objectiveFunction.NumberOfImages    ( )
        self.numberOfImageVariables = objectiveFunction.NumberOfVariables ( )
        if fixedTerminalImages: self.numberOfVariables = ( self.numberOfImages - 2 ) * self.numberOfImageVariables
        else:                   self.numberOfVariables =   self.numberOfImages       * self.numberOfImageVariables
        self.objectiveFunction = objectiveFunction
        # . Read the trajectory into the path.
        self.path    = ChainOfStatesPath ( self.numberOfImages, self.numberOfImageVariables )
        self.path.Load ( objectiveFunction )
        # . Allocate remaining space.
        self.tangent = Real1DArray ( self.numberOfImageVariables ) ; self.tangent.Set ( 0.0 )
        # . Finish up.
        return self

    def SemiActiveImages ( self ):
        """Determine a list of the semi-active images."""
        neighbors = set ( )
        for image in self.activeImages:
            lower = image - 1
            upper = image + 1
            if lower > 0                      : neighbors.add ( lower )
            if upper < self.numberOfImages - 1: neighbors.add ( upper )
        semiActive = list ( neighbors - set ( self.activeImages ) )
        semiActive.sort ( )
        return semiActive

#===================================================================================================================================
# . Testing.
#===================================================================================================================================
if __name__ == "__main__" :
    pass

