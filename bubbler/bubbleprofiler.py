"""
Interface to BubbleProfiler
===========================

>>> ginac_potential = "0.1*((-x + 2)^4 - 14*(-x + 2)^2 + 24*(-x + 2))"
>>> from potential import Potential
>>> solve(Potential(ginac_potential))
"""


from timer import clock
from subprocess32 import check_output
import os
import tempfile
import numpy as np


def solve(potential,
          output=None,
          n_spline_samples=100,
          n_knots=10,
          r_min=1E-4,
          r_max=1E1):
    """
    :param potential: Potential object or string
    :returns: Action, trajectory of bounce, time taken and extra information
    :rtype: tuple
    """

    # System call to BubblerProfiler executable

    output = output if output else tempfile.mkdtemp()

    field_names = " ".join(["--field '{}'".format(n)
                            for n in potential.field_names])
    false_vacuum = " ".join(["--local-minimum {}".format(v)
                             for v in potential.false_vacuum])
    true_vacuum = " ".join(["--global-minimum {}".format(v)
                            for v in potential.true_vacuum])

    template = ("{0}/bin/run_cmd_line_potential --force-output "
                "--potential '{1}' "
                "{2} "
                "--output-path {3} "
                "--grid-points {4} "
                "--knots {5} "
                "--domain-start {6} "
                "--domain-end {7} "
                "{8} "
                "{9} "
                "> /dev/null")

    command = template.format(os.environ["BUBBLEPROFILER"],
                              potential.ginac_potential,
                              field_names,
                              output,
                              n_spline_samples,
                              n_knots,
                              r_min,
                              r_max,
                              false_vacuum,
                              true_vacuum)
    try:
        with clock() as time:
            check_output(command, shell=True)
    except Exception as error:
        raise RuntimeError("BubbleProfiler crashed: {}".format(error))

    # Read action from text files

    action_file = "{}/action.txt".format(output)
    action = np.loadtxt(action_file, usecols=[1])[-1]

    # Read fields from text files

    field_file = "{}/field_profiles.txt".format(output)
    trajectory_data = np.loadtxt(field_file)
    max_iter = trajectory_data[:, 0].max()
    where = np.where(trajectory_data[:, 0] == max_iter)
    trajectory_data = trajectory_data[where, 1:][0]

    return action, trajectory_data, time.time, command

if __name__ == "__main__":
    import doctest
    doctest.testmod()