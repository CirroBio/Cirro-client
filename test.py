from cirro_api_client.v1.models import CustomProcessInput, Executor, PipelineCode, \
    FileMappingRule, FileNamePattern, RepositoryType, CustomPipelineSettings
from cirro.cirro_client import CirroApi

cirro = CirroApi()

# New pipeline
new_pipeline = CustomProcessInput(
    id="my_pipeline",
    name="My Pipeline",
    description="This is a test pipeline",
    executor=Executor.CROMWELL,
    category="DNA Sequencing",
    child_process_ids=[],
    parent_process_ids=["rnaseq"],
    documentation_url="https://example.com/docs",
    pipeline_code=PipelineCode(
        repository_path="CirroBio/test-pipeline",
        version="v1.0.0",
        entry_point="main.nf",
        repository_type=RepositoryType.GITHUB_PUBLIC
    ),
    linked_project_ids=[],
    is_tenant_wide=True,
    allow_multiple_sources=True,
    uses_sample_sheet=True,
    # This can be the same or different from the pipeline_code
    custom_settings=CustomPipelineSettings(
        repository="CirroBio/test-pipeline",
        branch="v1.0.0",
        repository_type=RepositoryType.GITHUB_PUBLIC,
    ),
    file_mapping_rules=[
        FileMappingRule(
            description="Filtered Feature Matrix",
            min_=1,
            file_name_patterns=[
                FileNamePattern(
                    example_name="filtered_feature_bc_matrix.h5",
                    description="Matrix",
                    sample_matching_pattern="(?P<sampleName>[\S ]*)/outs/filtered_feature_bc_matrix\.h5.csv"
                )
            ]
        )
    ]
)

cirro.processes.create_custom_process(new_pipeline)

# New data type
new_data_type = CustomProcessInput(
    id="images_jpg",
    name="JPG Images",
    description="Used for generic JPG images",
    executor=Executor.INGEST,
    child_process_ids=[],
    parent_process_ids=[],
    documentation_url="https://example.com/docs",
    linked_project_ids=["project_id_1", "project_id_2"],
    file_mapping_rules=[
        FileMappingRule(
            description="Images",
            file_name_patterns=[
                FileNamePattern(
                    example_name="image.jpg",
                    description="JPG Image",
                    sample_matching_pattern="(?P<sampleName>[\S ]*)/outs/image\.jpg"
                )
            ]
        )
    ]
)
cirro.processes.create_custom_process(new_data_type)
