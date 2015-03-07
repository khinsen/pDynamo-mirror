"""Pathway test systems."""

import os.path

from pBabel           import AmberCrdFile_ToCoordinates3, AmberTopologyFile_ToSystem, MOLFile_ToSystem, XYZFile_ToCoordinates3, XYZFile_ToSystem
from pCore            import CPUTime, logFile, LogFileActive
from pMolecule        import MMModelOPLS, NBModelFull, QCModelMNDO, QCModelORCA
from pMoleculeScripts import GrowingStringInitialPath

# . Should check barriers somehow?

#===================================================================================================================================
# . Parameters.
#===================================================================================================================================
# . Test systems.
# . Reactant and product energies are OK to 0.1 kJ mol^-1, barrier energies to 1.0 kJ mol^-1.
_PathTestSystemData = ( # . Alanine dipeptide.
                        { "energyBarrier"        : -131.0                              ,
                          "energyProduct"        : -165.0                              ,
                          "energyReactant"       : -133.1                              ,
                          "mmModel"              : MMModelOPLS ( "bookSmallExamples" ) ,
                          "nbModel"              : NBModelFull ( )                     ,
                          "productsFile"         : "bAla_c5.xyz"                       ,
                          "reactantsFile"        : "bAla_alpha.xyz"                    ,
                          "setUpCoordinatesFile" : "bAla_c7eq.mol"                     ,
                          "setUpMode"            : "mol"                               },
                        { "energyBarrier"        : -129.0                              ,
                          "energyProduct"        : -154.7                              ,
                          "energyReactant"       : -133.1                              ,
                          "mmModel"              : MMModelOPLS ( "bookSmallExamples" ) ,
                          "nbModel"              : NBModelFull ( )                     ,
                          "productsFile"         : "bAla_c7ax.xyz"                     ,
                          "reactantsFile"        : "bAla_alpha.xyz"                    ,
                          "setUpCoordinatesFile" : "bAla_c7eq.mol"                     ,
                          "setUpMode"            : "mol"                               },
                        { "energyBarrier"        : -132.0                              ,
                          "energyProduct"        : -168.4                              ,
                          "energyReactant"       : -133.1                              ,
                          "mmModel"              : MMModelOPLS ( "bookSmallExamples" ) ,
                          "nbModel"              : NBModelFull ( )                     ,
                          "productsFile"         : "bAla_c7eq.xyz"                     ,
                          "reactantsFile"        : "bAla_alpha.xyz"                    ,
                          "setUpCoordinatesFile" : "bAla_c7eq.mol"                     ,
                          "setUpMode"            : "mol"                               },
                        { "energyBarrier"        : -138.0                              ,
                          "energyProduct"        : -154.7                              ,
                          "energyReactant"       : -165.0                              ,
                          "mmModel"              : MMModelOPLS ( "bookSmallExamples" ) ,
                          "nbModel"              : NBModelFull ( )                     ,
                          "productsFile"         : "bAla_c7ax.xyz"                     ,
                          "reactantsFile"        : "bAla_c5.xyz"                       ,
                          "setUpCoordinatesFile" : "bAla_c7eq.mol"                     ,
                          "setUpMode"            : "mol"                               },
                        { "energyBarrier"        : -160.0                              ,
                          "energyProduct"        : -168.4                              ,
                          "energyReactant"       : -165.0                              ,
                          "mmModel"              : MMModelOPLS ( "bookSmallExamples" ) ,
                          "nbModel"              : NBModelFull ( )                     ,
                          "productsFile"         : "bAla_c7eq.xyz"                     ,
                          "reactantsFile"        : "bAla_c5.xyz"                       ,
                          "setUpCoordinatesFile" : "bAla_c7eq.mol"                     ,
                          "setUpMode"            : "mol"                               },
                        { "energyBarrier"        : -141.0                              ,
                          "energyProduct"        : -168.4                              ,
                          "energyReactant"       : -154.7                              ,
                          "mmModel"              : MMModelOPLS ( "bookSmallExamples" ) ,
                          "nbModel"              : NBModelFull ( )                     ,
                          "productsFile"         : "bAla_c7eq.xyz"                     ,
                          "reactantsFile"        : "bAla_c7ax.xyz"                     ,
                          "setUpCoordinatesFile" : "bAla_c7eq.mol"                     ,
                          "setUpMode"            : "mol"                               },
                        # . Cyclohexane.
                        { "energyBarrier"        :  179.0                              ,
                          "energyProduct"        :  143.8                              ,
                          "energyReactant"       :   81.8                              ,
                          "mmModel"              : MMModelOPLS ( "bookSmallExamples" ) ,
                          "nbModel"              : NBModelFull ( )                     ,
                          "productsFile"         : "cyclohexane_Twistboat.xyz"         ,
                          "reactantsFile"        : "cyclohexane_Chair.xyz"             ,
                          "setUpCoordinatesFile" : "cyclohexane.mol"                   ,
                          "setUpMode"            : "mol"                               },
                        { "energyBarrier"        : -607709.0                           ,
                          "energyProduct"        : -607732.3                           ,
                          "energyReactant"       : -607757.8                           ,
                          "isLong"               : True                                ,
                          "qcModel"              : QCModelORCA ( "HF:STO-3G", "SCFCONV10", useRandomJob = True ) ,
                          "productsFile"         : "cyclohexane_Twistboat_ORCA.xyz"    ,
                          "reactantsFile"        : "cyclohexane_Chair_ORCA.xyz"        ,
                          "setUpCoordinatesFile" : "cyclohexane_Chair_ORCA.xyz"        ,
                          "setUpMode"            : "xyz"                               },
                        # . Ratchet.
                        { "energyBarrier"        :  505.0             ,
                          "amberTopologyFile"    : "ratchet.top"      ,
                          "energyProduct"        :  431.6             ,
                          "energyReactant"       :  431.6             ,
                          "mmModel"              : MMModelOPLS ( )    ,
                          "nbModel"              : NBModelFull ( )    ,
                          "productsFile"         : "ratchet_2.xyz"    ,
                          "reactantsFile"        : "ratchet_1.xyz"    ,
                          "setUpCoordinatesFile" : "ratchet.crd"      ,
                          "setUpMode"            : "amber"            },
                        { "energyBarrier"        :  991.0             ,
                          "energyProduct"        :  901.8             ,
                          "energyReactant"       :  901.8             ,
                          "isLong"               : True               ,
                          "productsFile"         : "ratchetAM1_2.xyz" ,
                          "qcModel"              : QCModelMNDO ( )    ,
                          "reactantsFile"        : "ratchetAM1_1.xyz" ,
                          "setUpCoordinatesFile" : "ratchetAM1_1.xyz" ,
                          "setUpMode"            : "xyz"              },
                        # . Triazene.
                        { "energyBarrier"        :  154.0             ,
                          "energyProduct"        :  -71.7             ,
                          "energyReactant"       :  -71.7             ,
                          "productsFile"         : "triazene_2.xyz"   ,
                          "qcModel"              : QCModelMNDO ( )    ,
                          "reactantsFile"        : "triazene_1.xyz"   ,
                          "setUpCoordinatesFile" : "triazene.xyz"     ,
                          "setUpMode"            : "xyz"              } )

#===================================================================================================================================
# . Class.
#===================================================================================================================================
class PathTestSystem ( object ):
    """A path test system."""

    defaultAttributes = { "amberTopologyFile"    : None  ,
                          "dataPath"             : None  ,
                          "isLong"               : False ,
                          "mmModel"              : None  ,
                          "nbModel"              : None  ,
                          "products"             : None  ,
                          "productsFile"         : None  ,
                          "qcModel"              : None  ,
                          "reactants"            : None  ,
                          "reactantsFile"        : None  ,
                          "setUpCoordinatesFile" : None  ,
                          "setUpMode"            : None  ,
                          "system"               : None  ,
                          "tag"                  : None  }

    def __init__ ( self, **keywordArguments ):
        """Constructor."""
        for ( key, value ) in self.__class__.defaultAttributes.iteritems ( ): setattr ( self, key, value )
        for ( key, value ) in                 keywordArguments.iteritems ( ): setattr ( self, key, value )
        self.CheckAttributes ( )

    def CheckAttributes ( self ):
        """Check the attributes."""
        if self.dataPath is None:
            self.dataPath = os.path.join ( os.getenv ( "PDYNAMO_PMOLECULESCRIPTS" ), "data", "pathwayData" )
        if self.tag is None:
            name      = self.setUpCoordinatesFile[0:-4].split ( "_" )[0]
            reactants = self.reactantsFile[0:-4].split ( "_" )[-1]
            products  = self.productsFile[0:-4].split  ( "_" )[-1]
            self.tag = name + "_" + reactants + "_" + products

    def CheckStructures ( self, rmsGradientTolerance, log = logFile ):
        """Check the structures."""
        isOK = True
        save = self.system.coordinates3
        for coordinates3 in ( self.reactants, self.products ):
            self.system.coordinates3 = coordinates3
            self.system.Energy ( doGradients = True, log = log )
            isOK = isOK and ( self.system.configuration.energyTerms.rmsGradient <= rmsGradientTolerance )
        self.system.coordinates3 = save
        return isOK

    def GetGrowingStringInitialPath ( self, numberOfImages, trajectoryPath, log = logFile, sequence = "Alternate" ):
        """Get an initial path."""
        GrowingStringInitialPath ( self.system, numberOfImages, self.reactants, self.products, trajectoryPath, log = log, sequence = sequence )

    def GetSystem ( self, log = logFile ):
        """Get the system."""
        # . Set up the system with an MM model if it exists.
        if self.setUpMode == "amber":
            system              = AmberTopologyFile_ToSystem  ( os.path.join ( self.dataPath, self.amberTopologyFile    ), log = log, mmModel = self.mmModel )
            system.coordinates3 = AmberCrdFile_ToCoordinates3 ( os.path.join ( self.dataPath, self.setUpCoordinatesFile ), log = log )
        elif self.setUpMode == "mol":
            system = MOLFile_ToSystem ( os.path.join ( self.dataPath, self.setUpCoordinatesFile ) )
            if self.mmModel is not None: system.DefineMMModel ( self.mmModel )
        elif self.setUpMode == "xyz":
            system = XYZFile_ToSystem ( os.path.join ( self.dataPath, self.setUpCoordinatesFile ) )
        else:
            raise ValueError ( "Invalid set up mode: {:s}.".format ( self.setUpMode ) )
        # . Finish energy model set up.
        if self.qcModel is not None: system.DefineQCModel ( self.qcModel )
        if self.nbModel is not None: system.DefineNBModel ( self.nbModel )
        # . Get reactants and products.
        self.reactants = XYZFile_ToCoordinates3 ( os.path.join ( self.dataPath, self.reactantsFile ) )
        self.products  = XYZFile_ToCoordinates3 ( os.path.join ( self.dataPath, self.productsFile  ) )
        # . Finish up.
        self.system = system
        return system

#===================================================================================================================================
# . Generate a list with all test systems.
#===================================================================================================================================
PathTestSystems = []
for keywordArguments in _PathTestSystemData:
    PathTestSystems.append ( PathTestSystem ( **keywordArguments ) )

#===================================================================================================================================
# . Function.
#===================================================================================================================================
def PathTestReportsSummary ( reports, log = logFile ):
    """Summarize the results of a set of path tests."""
    # . Get number of converged tests.
    numberConverged = 0
    for report in reports.values ( ):
        if report.get ( "Converged", False ): numberConverged += 1
    # . Output.
    if LogFileActive ( log ):
        numberOfFunctionCalls = 0
        numberOfIterations    = 0
        totalTime             = 0.0
        tags = reports.keys ( )
        tags.sort ( )
        table = log.GetTable ( columns = [ 30, 20, 20, 20, 20 ] )
        table.Start   ( )
        table.Title   ( "Pathway Results Summary" )
        table.Heading ( "Path"           )
        table.Heading ( "Converged"      )
        table.Heading ( "Function Calls" )
        table.Heading ( "Iterations"     )
        table.Heading ( "Time"           )
        for tag in tags:
            report = reports[tag]
            table.Entry ( tag, alignment = "left" )
            table.Entry ( "{!r}".format ( report["Converged"     ] ) )
            table.Entry ( "{:d}".format ( report["Function Calls"] ) )
            table.Entry ( "{:d}".format ( report["Iterations"    ] ) )
            table.Entry ( CPUTime.TimeToString ( report["Time"] ) )
            numberOfFunctionCalls += report["Function Calls"]
            numberOfIterations    += report["Iterations"    ]
            totalTime             += report["Time"          ]
        table.Entry ( "Totals", alignment = "left" )
        table.Entry ( "{:d}/{:d}".format ( numberConverged, len ( reports ) ) )
        table.Entry ( "{:d}".format ( numberOfFunctionCalls ) )
        table.Entry ( "{:d}".format ( numberOfIterations    ) )
        table.Entry ( CPUTime.TimeToString ( totalTime ) )
        table.Stop ( )
    # . Finish up.
    return numberConverged

#===================================================================================================================================
# . Testing.
#===================================================================================================================================
if __name__ == "__main__":

    # . Check the structure for each test system.
    results = []
    for testSystem in PathTestSystems:
        testSystem.GetSystem ( )
        isOK = testSystem.CheckStructures ( 0.001 )
        results.append ( ( testSystem.tag, isOK ) )

    # . Output.
    print ( "\nResults of \"CheckStructures\":" )
    for ( tag, isOK ) in results:
        print ( "{:<30s} {:5s}".format ( tag, repr ( isOK ) ) )
