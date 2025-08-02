from glacium.api import Project
from glacium.utils.logging import log
proj = Project.load("Project01", "20250719-150505-013264-3CCA")
# proj.run("XFOIL_REFINE")
# proj.run("XFOIL_THICKEN_TE")
# proj.run("XFOIL_PW_CONVERT")
# proj.run("POINTWISE_GCI")
# proj.run("FLUENT2FENSAP")
# proj.run("MULTISHOT_RUN")
# proj.run("FENSAP_RUN")
# proj.run("FENSAP_CONVERGENCE_STATS")
# proj.run("DROP3D_RUN")
# proj.run("DROP3D_CONVERGENCE_STATS")
# proj.run("ICE3D_RUN")
# proj.run("ICE3D_CONVERGENCE_STATS")
# proj.add_job("POSTPROCESS_MULTISHOT")
#
# proj.run("POSTPROCESS_MULTISHOT")
proj.add_job("ANALYZE_MULTISHOT")

proj.run("ANALYZE_MULTISHOT")
log.info(proj.uid)
