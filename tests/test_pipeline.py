"""
Tests that focus on how the caching mechanism integrates with a pipeline of
functions, ensuring that the cache works correctly in a real-world scenario
involving multiple steps.
"""

import os

from pickled_pipeline.cache import _default_checkpoint_name


def test_pipeline(cache):
    # Define the pipeline functions using the test cache
    @cache.checkpoint()
    def step1_user_input(user_text):
        return user_text

    @cache.checkpoint()
    def step2_enhance_text(text):
        enhanced_text = text.upper()
        return enhanced_text

    @cache.checkpoint()
    def step3_produce_document(enhanced_text):
        document = f"Document based on: {enhanced_text}"
        return document

    @cache.checkpoint()
    def step4_generate_additional_documents(document):
        documents = [document + f" - Version {i}" for i in range(3)]
        return documents

    @cache.checkpoint()
    def step5_summarize_documents(documents):
        summary = f"Summary of documents: {', '.join(documents)}"
        return summary

    def run_pipeline(user_text):
        text = step1_user_input(user_text)
        enhanced_text = step2_enhance_text(text)
        document = step3_produce_document(enhanced_text)
        documents = step4_generate_additional_documents(document)
        summary = step5_summarize_documents(documents)
        return summary

    # Run the pipeline
    user_text = "Initial input from user."
    summary = run_pipeline(user_text)

    # Verify the output
    expected_summary = (
        "Summary of documents: "
        "Document based on: INITIAL INPUT FROM USER. - Version 0, "
        "Document based on: INITIAL INPUT FROM USER. - Version 1, "
        "Document based on: INITIAL INPUT FROM USER. - Version 2"
    )
    assert summary == expected_summary

    # Verify that cache files were created (excluding manifest)
    cache_files = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    assert len(cache_files) == 5

    # Truncate the cache from step3 onwards
    cache.truncate_cache(_default_checkpoint_name(step3_produce_document))

    # Ensure that only two cache files remain (excluding manifest)
    cache_files_after_truncate = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    assert len(cache_files_after_truncate) == 2

    # Re-run the pipeline (steps from step3 onwards should be recomputed)
    summary_new = run_pipeline(user_text)
    assert summary_new == expected_summary

    # Verify that all cache files are recreated (excluding manifest)
    cache_files_final = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    assert len(cache_files_final) == 5


def test_pipeline_with_different_input(cache):
    # Define the pipeline functions using the test cache
    @cache.checkpoint()
    def step1_user_input(user_text):
        return user_text

    @cache.checkpoint()
    def step2_enhance_text(text):
        enhanced_text = text.upper()
        return enhanced_text

    @cache.checkpoint()
    def step3_produce_document(enhanced_text):
        document = f"Document based on: {enhanced_text}"
        return document

    @cache.checkpoint()
    def step4_generate_additional_documents(document):
        documents = [document + f" - Version {i}" for i in range(3)]
        return documents

    @cache.checkpoint()
    def step5_summarize_documents(documents):
        summary = f"Summary of documents: {', '.join(documents)}"
        return summary

    def run_pipeline(user_text):
        text = step1_user_input(user_text)
        enhanced_text = step2_enhance_text(text)
        document = step3_produce_document(enhanced_text)
        documents = step4_generate_additional_documents(document)
        summary = step5_summarize_documents(documents)
        return summary

    # Run the pipeline with the first input
    user_text1 = "First input from user."
    summary1 = run_pipeline(user_text1)

    # Verify that cache files were created (excluding manifest)
    cache_files_after_first_run = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    num_cache_files_first_run = len(cache_files_after_first_run)
    assert num_cache_files_first_run == 5

    # Run the pipeline again with a different input
    user_text2 = "Second input from user."
    summary2 = run_pipeline(user_text2)

    # Verify that new cache files were created for the new input (excluding
    # manifest).
    cache_files_after_second_run = [
        filename
        for filename in os.listdir(cache.cache_dir)
        if filename != "cache_manifest.json"
    ]
    num_cache_files_second_run = len(cache_files_after_second_run)
    # Should have 5 new cache files.
    assert num_cache_files_second_run == 10

    # Ensure that the summaries are different
    assert summary1 != summary2
