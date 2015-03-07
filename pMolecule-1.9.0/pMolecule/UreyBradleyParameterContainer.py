#-------------------------------------------------------------------------------
# . File      : UreyBradleyParameterContainer.py
# . Program   : pDynamo-1.9.0                           (http://www.pdynamo.org)
# . Copyright : CEA, CNRS, Martin J. Field (2007-2014)
# . License   : CeCILL French Free Software License     (http://www.cecill.info)
#-------------------------------------------------------------------------------
"""Urey-Bradley parameter classes."""

from HarmonicBondContainer import HarmonicBondContainer
from MMParameterContainer  import MMParameterContainer
from pCore                 import UNITS_ENERGY_KILOCALORIES_PER_MOLE_TO_KILOJOULES_PER_MOLE

#===================================================================================================================================
# . Class.
#===================================================================================================================================
class UreyBradleyParameterContainer ( MMParameterContainer ):
    """A container for Urey-Bradley parameters."""

    defaultStrictAssignment = False
    defaultTermLabel        = "Urey-Bradley"

    def __getstate__ ( self ):
        """Get state as a mapping."""
        mapping = {}
        # . Columns.
        mapping["Parameter Fields"] = [ "Atom Type 1", "Atom Type 2", "Atom Type 3", "Equilibrium Value", "Force Constant" ]
        # . Rows.
        keys = self.rawItems.keys ( )
        keys.sort ( )
        rows = []
        for key in keys:
            ( eV, fC ) = self.rawItems[key]
            rows.append ( [ key[0], key[1], key[2], eV, fC ] )
        mapping["Parameter Values"] = rows
        # . Other data.
        if self.label is not None: mapping["Label"] = self.label
        for key in ( "Analytic Form", "Units" ):
            if key in self.properties:
                mapping[key] = self.properties[key]
        return mapping

    def __setstate__ ( self, mapping ):
        """Set state from a mapping."""
        # . There are assumed to be no errors!
        try:
            # . Basic construction.
            self.__init__ ( )
            columns         = mapping.pop ( "Parameter Fields" )
            rows            = mapping.pop ( "Parameter Values" )
            self.label      = mapping.pop ( "Label", None )
            self.properties = dict ( mapping )
            # . Get token indices.
            l1 = columns.index ( "Atom Type 1" )
            l2 = columns.index ( "Atom Type 2" )
            l3 = columns.index ( "Atom Type 3" )
            eV = columns.index ( "Equilibrium Value" )
            fC = columns.index ( "Force Constant"    )
            # . Create the raw items.
            self.rawItems = {}
            for row in rows:
                key = self.MakeKey ( row[l1], row[l2], row[l3] )
                self.rawItems[key] = ( float ( row[eV] ), float ( row[fC] ) )
            if len ( self.rawItems ) != len ( rows ): raise
            # . Create the items that are to be used.
            self.ProcessRawItems ( )
#        except Exception as e:
#            print e[0]
        except:
            raise ValueError ( "Error reconstructing instance of " + self.__class__.__name__ + "." )

    @staticmethod
    def MakeKey ( label1, label2, label3 ):
        """Make a key."""
        if ( label1 >= label3 ): return ( label1, label2, label3 )
        else:                    return ( label3, label2, label1 )

    def MakeMMTerms ( self, atomTypeLabels, termIndices ):
        """Make the appropriate MM terms given a list of term indices."""
        missingParameters = set ( )
        mmTerms           = []
        if len ( termIndices ) > 0:
            # . Initialization.
            parameterKeys = {}
            parameters    = []
            terms         = []
            # . Generate both term and parameter data.
            for ( i, j, k ) in termIndices:
                ti        = atomTypeLabels[i]
                tj        = atomTypeLabels[j]
                tk        = atomTypeLabels[k]
                key       = self.MakeKey ( ti, tj, tk )
                parameter = self.items.get ( key, None )
                if parameter is None:
                    if self.useStrictAssignment:
                        missingParameters.add ( ( self.termLabel, key ) )
                else:
                    p = parameterKeys.get ( key, -1 )
                    if p == -1:
                        p = len ( parameterKeys )
                        parameterKeys[key] = p
                        parameters.append ( ( parameter[0], parameter[1] ) )
                    terms.append ( ( i, k, p, True ) )
            # . Construct the parameter keys.
            newKeys = [ None for i in range ( len ( parameterKeys ) ) ]
            for ( key, value ) in parameterKeys.iteritems ( ):
                newKeys[value] = self.keySeparator.join ( key )
            # . Construct the container.
            numberOfParameters = len ( parameters )
            numberOfTerms      = len ( terms      ) 
            if ( numberOfParameters > 0 ) and ( numberOfTerms > 0 ) and ( len ( missingParameters ) <= 0 ):
                state = { "is12Interaction" : False          ,
                          "label"           : self.termLabel ,
                          "parameterKeys"   : newKeys        ,
                          "parameters"      : parameters     ,
                          "terms"           : terms          }
                mm = HarmonicBondContainer.Raw ( )
	        mm.__setstate__ ( state )
                mm.Sort ( )
                mmTerms.append ( mm )
        return ( mmTerms, missingParameters )

    def MakeMMTermsFromConnectivity ( self, atomTypeLabels, connectivity ):
        """Make the appropriate MM terms given a connectivity."""
        termIndices = connectivity.GetAngleIndices ( )
        return self.MakeMMTerms ( atomTypeLabels, termIndices )

    def ProcessRawItems ( self ):
        """Process the raw items."""
        # . Create the items that are to be used and convert to the correct units if necessary.
        units   = self.properties.get ( "Units", None )
        convert = ( units is not None ) and ( units.get ( "Force Constant", "" ).find ( "kcal" ) > -1 )
        if convert:
            self.items = {}
            for ( key, ( eV, fC ) ) in self.rawItems.iteritems ( ):
                self.items[key] = ( eV, fC * UNITS_ENERGY_KILOCALORIES_PER_MOLE_TO_KILOJOULES_PER_MOLE )
        else:
            self.items = self.rawItems

#===================================================================================================================================
# . Testing.
#===================================================================================================================================
if __name__ == "__main__" :
    pass
