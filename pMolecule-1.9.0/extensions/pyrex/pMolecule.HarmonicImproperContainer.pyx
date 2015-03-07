#-------------------------------------------------------------------------------
# . File      : pMolecule.HarmonicImproperContainer.pyx
# . Program   : pDynamo-1.9.0                           (http://www.pdynamo.org)
# . Copyright : CEA, CNRS, Martin J. Field (2007-2014)
# . License   : CeCILL French Free Software License     (http://www.cecill.info)
#-------------------------------------------------------------------------------
"""A container for Harmonic impropers."""

from pCore import Clone, logFile, LogFileActive

#===================================================================================================================================
# . Class.
#===================================================================================================================================
cdef class HarmonicImproperContainer ( MMTerm ):

    # . Public methods.
    def __copy__ ( self ):
        """Copying."""
        cdef HarmonicImproperContainer new
        new               = self.__class__.Raw ( )                           
        new.label         = self.label                                       
        new.cObject       = HarmonicImproperContainer_Clone ( self.cObject ) 
        new.isOwner       = True                                             
        new.parameterKeys = Clone ( self.parameterKeys )
        return new

    def __dealloc__ ( self ):
        """Finalization."""
        if self.isOwner:
            HarmonicImproperContainer_Deallocate ( &self.cObject )
            self.isOwner = False

    def __deepcopy__ ( self, memo ):
        """Copying."""
        return self.__copy__ ( )

    def __getmodule__ ( self ):
        """Return the module name."""
        return "pMolecule.HarmonicImproperContainer"

    def __getstate__ ( self ):
        """Return the state."""
        cdef Integer i
        # . Parameters.
        parameterFields = [ "equilibriumValue", "forceConstant" ]
        parameters      = []
        for i from 0 <= i < self.cObject.nparameters:
            parameters.append ( [ self.cObject.parameters[i].eq ,
                                  self.cObject.parameters[i].fc ] )
        # . Terms.
        termFields = [ "atom1", "atom2", "atom3", "atom4", "parameter", "isActive" ]
        terms      = []
        for i from 0 <= i < self.cObject.nterms:
            terms.append ( [ self.cObject.terms[i].atom1 ,
                             self.cObject.terms[i].atom2 ,
                             self.cObject.terms[i].atom3 ,
                             self.cObject.terms[i].atom4 ,
                             self.cObject.terms[i].type  ,
                             self.cObject.terms[i].QACTIVE == CTrue ] )
        # . State.
        state = { "label"           : self.label      ,
                  "parameterFields" : parameterFields ,
                  "parameters"      : parameters      ,
                  "termFields"      : termFields      ,
                  "terms"           : terms           }
        if self.parameterKeys is not None: state["parameterKeys"] = self.parameterKeys
        return state

    def __init__ ( self, numberOfParameters, numberOfTerms, label = "Harmonic Improper" ):
        """Constructor."""
        self._Initialize ( )
        self._Allocate ( numberOfParameters, numberOfTerms )
        self.label = label

    def __setstate__ ( self, state ):
        """Set the state."""
        cdef Integer i
        # . Allocate the object.
        parameters = state["parameters"]
        terms      = state["terms"     ]
        self._Allocate ( len ( parameters ), len ( terms ) )
        if "label" in state: self.label = state["label"]
        self.parameterKeys = state.get ( "parameterKeys", None )
        # . Fill the object.
        # . Parameters.
        for ( i, ( eq, fc ) ) in enumerate ( parameters ):
            self.cObject.parameters[i].eq = eq
            self.cObject.parameters[i].fc = fc
        # . Terms.
        for ( i, ( a1, a2, a3, a4, p, q ) ) in enumerate ( terms ):
            self.cObject.terms[i].atom1 = a1
            self.cObject.terms[i].atom2 = a2
            self.cObject.terms[i].atom3 = a3
            self.cObject.terms[i].atom4 = a4
            self.cObject.terms[i].type  = p
            if q: self.cObject.terms[i].QACTIVE = CTrue
            else: self.cObject.terms[i].QACTIVE = CFalse
        # . Finish processing.
        self.FillCosSinValues ( )

    def _Allocate ( self, numberOfParameters, numberOfTerms ):
        """Allocation."""
        self.cObject = HarmonicImproperContainer_Allocate ( numberOfTerms, numberOfParameters )
        self.isOwner = True

    def _Initialize ( self ):
        """Initialization."""
        self.cObject       = NULL
        self.isOwner       = False
        self.label         = "Harmonic Improper"
        self.parameterKeys = None

    def ActivateTerms ( self ):
        """Activate terms."""
        HarmonicImproperContainer_ActivateTerms ( self.cObject )

    def DeactivateFixedAtomTerms ( self, Selection fixedatoms ):
        """Deactivate terms involving fixed atoms."""
        if fixedatoms is not None: HarmonicImproperContainer_DeactivateFixedAtomTerms ( self.cObject, fixedatoms.cObject )

    def DeactivateQCAtomTerms ( self, Selection qcAtoms, Selection boundaryatoms ):
        """Deactivate terms involving QC atoms."""
        if qcAtoms is not None: HarmonicImproperContainer_DeactivateQCAtomTerms ( self.cObject, qcAtoms.cObject, NULL )

    def Energy ( self, Coordinates3 coordinates3, Coordinates3 gradients3 ):
        """Energy and gradients."""
        if gradients3 is None: energy = HarmonicImproperContainer_Energy ( self.cObject, coordinates3.cObject, NULL               )
        else:                  energy = HarmonicImproperContainer_Energy ( self.cObject, coordinates3.cObject, gradients3.cObject )
        return ( self.label, energy )

    def FillCosSinValues ( self ):
        """Fill the cos and sin phases of the parameter array."""
        HarmonicImproperContainer_FillCosSinValues ( self.cObject )

    def GetUniqueTermIndices ( self ):
        """Return the term indices."""
        cdef Integer i
        indices = []
        for i from 0 <= i < self.cObject.nterms:
            indices.append ( self.cObject.terms[i].atom1 )
            indices.append ( self.cObject.terms[i].atom2 )
            indices.append ( self.cObject.terms[i].atom3 )
            indices.append ( self.cObject.terms[i].atom4 )
        return ( self.cObject.nterms, indices )

    def Merge ( self, items, information = {} ):
        """Merging - slow version."""
        # . Initialization.
        new = None
        # . Get the selection increments.
        increments = information.get ( "atomIncrements", None )
        # . Do the merge.
        if increments is not None:
            # . Gather terms.
            doKeys        = True
            np            = 0
            parameterKeys = []
            parameters    = []
            terms         = []
            for ( increment, item ) in zip ( increments, [ self ] + items ):
                state       = item.__getstate__ ( )
                if np == 0:
                    parameterFields = state["parameterFields"]
                    termFields      = state["termFields"     ]
                parameterKeys0 = state.get ( "parameterKeys", None )
                parameters0    = state["parameters"]
                terms0         = state["terms"     ]
                np0            = len ( parameters0 )
                parameters.extend ( parameters0 )
                for ( a1, a2, a3, a4, p, q ) in terms0:
                    terms.append ( ( a1 + increment ,
                                     a2 + increment ,
                                     a3 + increment ,
                                     a4 + increment ,
                                     p  + np , q ) )
                if parameterKeys0 is None: doKeys = False
                else: parameterKeys.extend ( parameterKeys0 )
                np = np + np0
            # . Construct the new keys and parameters.
            if doKeys:
                ( doKeys, oldToNew, parameterKeys, parameters ) = self.MergeKeys ( parameterKeys, parameters )
            else:
                parameterKeys = None
            # . Construct the object.
            state = { "label"           : self.label      ,
                      "parameterFields" : parameterFields ,
                      "parameterKeys"   : parameterKeys   ,
                      "parameters"      : parameters      ,
                      "termFields"      : termFields      ,
                      "terms"           : terms           }
            new = self.__class__.Raw ( )
            new.__setstate__ ( state )
            # . Reindex.
            if doKeys: new.ResetTermTypes ( oldToNew )
        return new

    def NumberOfParameters ( self ):
        """Return the number of parameters."""
        if self.cObject == NULL: return 0
        else:                    return self.cObject.nparameters

    def NumberOfTerms ( self ):
        """Return the number of terms."""
        if self.cObject == NULL: return 0
        else:                    return self.cObject.nterms

    def Prune ( self, Selection selection, information = {} ):
        """Pruning."""
        cdef HarmonicImproperContainer new
        new               = HarmonicImproperContainer.Raw ( )
        new.cObject       = HarmonicImproperContainer_Prune ( self.cObject, selection.cObject )
        new.isOwner       = True
        new.label         = self.label
        new.parameterKeys = self.parameterKeys
        if new.cObject == NULL: return None
        else:                   return new

    def ResetTermTypes ( self, mapping ):
        """Reset term types."""
        cdef Integer i
        for i from 0 <= i < self.cObject.nterms:
            iOld = self.cObject.terms[i].type
            self.cObject.terms[i].type = mapping[iOld]

    def Sort ( self ):
        """Sorting."""
        HarmonicImproperContainer_Sort ( self.cObject )

    def SummaryEntry ( self, summary ):
        """Summary entry."""
        cdef Integer n
        if summary is not None:
            n = HarmonicImproperContainer_NumberOfInactiveTerms ( self.cObject )
            summary.Entry ( self.label + " Terms",      "{:d}".format ( self.cObject.nterms      ) )
            summary.Entry ( self.label + " Parameters", "{:d}".format ( self.cObject.nparameters ) )
            if n > 0: summary.Entry ( self.label + " Inactive", "{:d}".format ( n ) )

    def UpperBound ( self ):
        return HarmonicImproperContainer_UpperBound ( self.cObject )
