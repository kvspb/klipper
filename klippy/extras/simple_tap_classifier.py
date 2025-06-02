from . import load_cell_probe
from .load_cell_probe import ValidationError


# Naive tap classifier rules:
# 1) It should pass initial TapAnalysis as a valid tap
# 2) The compression force must be least the trigger force
# 3) The decompression line force should be at least 2/3s of the
#    minimum compression force + 1/3 of any additional compression force
# 4) There should be less than a 20% difference in force between the collision
#    and the pullback elbows relative to the compression force.
# Optional elbow sharpness checks:
# 5) Check collision elbow sharpness
# 6) Check pullback elbow sharpness
class SimpleTapClassifier(load_cell_probe.TapClassifierModule):
    def __init__(self, config):
        self.printer = config.get_printer()
        self.min_decomp_force_pct = 0.01 * config.getfloat(
            'min_decompression_force_percentage',
            minval=20., default=66.66, maxval=100.)
        self.max_baseline_change_pct = 0.01 * config.getfloat(
            'max_baseline_force_change_percentage',
            above=0., maxval=50., default=20.)

    def classify(self, tap_analysis):
        # This module cant rescue bad data
        if len(tap_analysis.get_errors()) > 0:
            return

        trigger_force = tap_analysis.get_trigger_force()
        # compression line check
        tap_points = tap_analysis.get_tap_points()
        comp_start = tap_points[1]
        comp_end = tap_points[2]
        compression_force = abs(comp_end.force - comp_start.force)
        if compression_force < trigger_force:
            tap_analysis.get_errors().append("INSUFFICIENT_COMPRESSION_FORCE")

        # decompression line check
        decomp_start = tap_points[3]
        decomp_end = tap_points[4]
        decompression_force = abs(decomp_start.force - decomp_end.force)
        min_decompression_force = (
                (trigger_force * self.min_decomp_force_pct) +
                ((compression_force - trigger_force) * 0.33))
        if decompression_force < min_decompression_force:
            tap_analysis.get_errors().append("INSUFFICIENT_DECOMPRESSION_FORCE")

        # baseline check
        baseline_force_delta = abs(comp_start.force - decomp_end.force)
        max_baseline_delta = compression_force * self.max_baseline_change_pct
        if baseline_force_delta > max_baseline_delta:
            tap_analysis.get_errors().append("BASELINE_FORCE_INCONSISTENT")

        if len(tap_analysis.get_errors()) > 0:
            tap_analysis.set_is_valid(False)


def load_config(config):
    return SimpleTapClassifier(config)
