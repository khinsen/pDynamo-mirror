"""Get information about possible solvation scenarios."""

import os, os.path, sys
sys.path.append ( os.path.join ( os.path.dirname ( os.path.realpath ( __file__ ) ), "..", "data" ) )

from Definitions      import outPath
from pCore            import Unpickle
from pMoleculeScripts import DetermineSolvationParameters

# . Get the system.
system = Unpickle ( os.path.join ( outPath, "step7.pkl" ) )
system.Summary ( )

# . Determine solvation parameters.
DetermineSolvationParameters ( system )
