from recipes.almahelpers import fixsyscaltimes # SACM/JAO - Fixes
__rethrow_casa_exceptions = True
context = h_init()
context.set_state('ProjectSummary', 'proposal_code', '2017.1.01355.L')
context.set_state('ProjectSummary', 'piname', 'unknown')
context.set_state('ProjectSummary', 'proposal_title', 'unknown')
context.set_state('ProjectStructure', 'ous_part_id', 'X1760161662')
context.set_state('ProjectStructure', 'ous_title', 'Undefined')
context.set_state('ProjectStructure', 'ppr_file', '/opt/dared/opt/c5r1/mnt/dataproc/2017.1.01355.L_2018_05_13T12_06_17.126/SOUS_uid___A001_X1296_X14b/GOUS_uid___A001_X1296_X14c/MOUS_uid___A001_X1296_X153/working/PPR_uid___A001_X1296_X154.xml')
context.set_state('ProjectStructure', 'ps_entity_id', 'uid://A001/X1220/Xddd')
context.set_state('ProjectStructure', 'recipe_name', 'hsd_calimage')
context.set_state('ProjectStructure', 'ous_entity_id', 'uid://A001/X1220/Xdd9')
context.set_state('ProjectStructure', 'ousstatus_entity_id', 'uid://A001/X1296/X153')
try:
    hsd_importdata(vis=['uid___A002_Xcc3ae3_X11aa8', 'uid___A002_Xcccc19_Xa854', 'uid___A002_Xcd1950_X2f15', 'uid___A002_Xcd3dcc_X1a3b', 'uid___A002_Xcd4e14_X1b27'], session=['session_1', 'session_2', 'session_3', 'session_4', 'session_6'])
    hsd_flagdata(pipelinemode="automatic")
    h_tsyscal(pipelinemode="automatic")
    hsd_tsysflag(pipelinemode="automatic")
    hsd_skycal(pipelinemode="automatic")
    hsd_k2jycal(pipelinemode="automatic")
    hsd_applycal(pipelinemode="automatic")
    hsd_baseline(pipelinemode="automatic")
    hsd_blflag(pipelinemode="automatic")
    hsd_baseline(pipelinemode="automatic")
    hsd_blflag(pipelinemode="automatic")
    hsd_imaging(pipelinemode="automatic")
finally:
    h_save()