from .base import correct
from .none import none_correct
from .volcano_scan import volcano_scan
from .beer_lambert import beer_lambert
from .lambert_albedo import lambert_albedo

REGISTRY = {
    "none": none_correct,
    "volcano_scan": volcano_scan,
    "beer_lambert": beer_lambert,
    "lambert_albedo": lambert_albedo,
}
