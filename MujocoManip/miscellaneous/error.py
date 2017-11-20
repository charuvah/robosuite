class MujocoManipError(Exception):
    """Base class for exceptions in MujocoManipulation."""
    pass

class XMLError(MujocoManipError):
    """Exception raised for errors related to xml."""
    pass

class SimulationError(MujocoManipError):
    """Exception raised for errors during runtime."""
    pass