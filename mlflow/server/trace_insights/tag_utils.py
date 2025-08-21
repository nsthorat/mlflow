"""Shared utilities for tag discovery and filtering in MLflow Trace Insights"""

def should_filter_tag(tag_key: str) -> bool:
    """
    Determine if a tag should be filtered out as a built-in MLflow tag.
    
    Args:
        tag_key: The tag key to check
        
    Returns:
        True if the tag should be filtered out (excluded), False if it should be included
    """
    return tag_key.startswith("mlflow") or "tag.mlflow" in tag_key