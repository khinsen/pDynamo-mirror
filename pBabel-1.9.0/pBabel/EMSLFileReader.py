#-------------------------------------------------------------------------------
# . File      : EMSLFileReader.py
# . Program   : pDynamo-1.9.0                           (http://www.pdynamo.org)
# . Copyright : CEA, CNRS, Martin J. Field (2007-2014)
# . License   : CeCILL French Free Software License     (http://www.cecill.info)
#-------------------------------------------------------------------------------
"""Handle EMSL Gaussian basis set files.

This module reads EMSL basis set files in Gaussian94
format. These files may be downloaded from the Gaussian
Basis Set Order Form run by the Environmental and Molecular
Science Laboratory at the Pacific Northwest Laboratories.
"""

from pCore     import logFile, LogFileActive, TextFileReader
from pMolecule import GaussianBasis, PeriodicTable

#===================================================================================================================================
# . Parameters.
#===================================================================================================================================
# . The recognized shell types.
_ShellTypes = [ "S", "SP", "SPD", "SPDF", "SPDFG", "P", "D", "F", "G" ]

#===================================================================================================================================
# . Class.
#===================================================================================================================================
class EMSLG94FileReader ( TextFileReader ):
    """The class for reading EMSL basis set files in Gaussian94 format."""

    def Parse ( self, log = logFile ):
        """Parse the data on the file."""
        if not self.QPARSED:
            # . Initialization.
            if LogFileActive ( log ): self.log = log
            # . Open the file.
            self.Open ( )
            # . Read the raw data.
            try:
                basis = []
                bases = []
                for ( iline, line ) in enumerate ( self.file ):
                    line = line.strip ( )
                    if len ( line ) <= 0: continue
                    # . Header line.
                    elif line.startswith ( "BASIS" ):
                        self.basisname = line[7:-1]
                    # . Terminator line.
                    elif line == "****":
                        if len ( basis ) > 0: bases.append ( basis )
                        basis = []
                    # . General line.
                    else:
                        basis.append ( ( iline, line ) )
            except EOFError:
                pass
            # . Process the data.
            self._ProcessRawData ( bases )
	    # . Close the file.
            self.WarningStop ( )
	    self.Close ( )
            # . Set the parsed flag and some other options.
            self.log     = None
            self.QPARSED = True

    def ToGaussianBases ( self, isSpherical = True ):
        """Return the gaussian bases from the file."""
        if self.QPARSED:
            if not hasattr ( self, "gaussianbases" ):
                self.gaussianbases = []
                if self.bases is not None:
                    for ( atomicNumber, shells ) in self.bases:
                        basis  = GaussianBasis.Uninitialized ( atomicNumber, len ( shells ), isSpherical = isSpherical )
                        ishell = 0
                        for ( shellid, nprimitives, scale, primitives ) in shells:
                            basis.AllocateShell ( ishell, shellid, nprimitives )
                            coefficients = []
                            exponents    = []
                            for i in range ( len ( shellid ) ): coefficients.append ( [] )
                            for primitive in primitives:
                                exponents.append    ( primitive[0] )
                                for i in range ( len ( shellid ) ): coefficients[i].append ( primitive[i+1] )
                            for ( i, c ) in enumerate ( shellid ):
                                basis.SetShellCoefficients ( ishell, c, coefficients[i] )
                            basis.SetShellExponents ( ishell, exponents, scale = scale )
                            ishell += 1
                        self.gaussianbases.append ( basis )
            return self.gaussianbases
        else:
            return None

    def _ProcessRawData ( self, bases ):
        """Process the input basis lines."""
        # . Process the text data.
        self.bases = []
        for basis in bases:
            # . Title line.
            ( iline, line ) = basis.pop ( 0 )
            words           = line.split ( )
            atomicNumber    = PeriodicTable.AtomicNumber ( words[0] )
            if atomicNumber <= 0: self.Warning ( "Invalid element, {:s}, for basis on line {:d}.".format ( words[0], iline ), True )
            # . Shell lines.
            shells = []
            while len ( basis ) > 0:
                # . Header.
                ( iline, line ) = basis.pop ( 0 )
                words           = line.split ( )
                shellid         = words[0].upper ( )
                if shellid not in _ShellTypes: self.Warning ( "Unrecognized shell type, {:s}, for basis on line {:d}.".format ( shellid, iline ), True )
                nprimitives     = int   ( words[1] )
                scale           = float ( words[2] )
                # . Primitive lines.
                primitives = []
                if len ( basis ) >= nprimitives:
                    for p in range ( nprimitives ):
                        primitive       = []
                        ( iline, line ) = basis.pop ( 0 )
                        words           = line.split ( )
                        if ( len ( words ) != ( len ( shellid ) + 1 ) ): self.Warning ( "Invalid number of primitive data on line {:d}.".format ( iline ), True )
                        for word in words: primitive.append ( float ( word ) )
                        primitives.append ( primitive )
                else: self.Warning ( "Invalid number of primitives for basis on line {:d}.".format ( iline ), True )
                # . Save the data.
                shells.append ( ( shellid, nprimitives, scale, primitives ) )
            # . Save the basis.
            self.bases.append ( ( atomicNumber, shells ) )

#===================================================================================================================================
# . Helper function.
#===================================================================================================================================
def EMSLG94File_ToGaussianBases ( filename, isSpherical = True, log = logFile ):
    """Helper function that reads Gaussian basis sets in G94 format from an EMSL file."""
    infile = EMSLG94FileReader ( filename )
    infile.Parse ( log = log )
    bases = infile.ToGaussianBases ( isSpherical = isSpherical )
    return bases

#===================================================================================================================================
# . Testing.
#===================================================================================================================================
if __name__ == "__main__":
    pass
