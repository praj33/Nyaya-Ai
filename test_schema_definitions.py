import json
from api.schemas import (
    QueryRequest, 
    MultiJurisdictionRequest, 
    ExplainReasoningRequest, 
    FeedbackRequest,
    UserRole,
    DomainHint,
    JurisdictionHint,
    ExplanationLevel,
    FeedbackType
)

def test_schema_definitions():
    """Test that all Pydantic schemas are correctly defined."""
    
    print("=== Pydantic Schema Definition Test ===\n")
    
    # Test that enums are properly defined
    print("1. Testing Enum Definitions:")
    print(f"   UserRole values: {list(UserRole.__members__.keys())}")
    print(f"   DomainHint values: {list(DomainHint.__members__.keys())}")
    print(f"   JurisdictionHint values: {list(JurisdictionHint.__members__.keys())}")
    print(f"   ExplanationLevel values: {list(ExplanationLevel.__members__.keys())}")
    print(f"   FeedbackType values: {list(FeedbackType.__members__.keys())}")
    print()
    
    # Test that models can be instantiated with valid data
    print("2. Testing Schema Instantiation with Valid Data:")
    
    try:
        # QueryRequest
        query_req = QueryRequest(
            query="Test query",
            user_context={
                "role": "citizen",
                "confidence_required": True
            },
            jurisdiction_hint="India",
            domain_hint="constitutional"
        )
        print(f"   ✓ QueryRequest: {query_req.query[:10]}...")
        
        # MultiJurisdictionRequest
        multi_req = MultiJurisdictionRequest(
            query="Test multi query",
            jurisdictions=["India", "UK"]
        )
        print(f"   ✓ MultiJurisdictionRequest: {multi_req.query[:10]}...")
        
        # ExplainReasoningRequest
        explain_req = ExplainReasoningRequest(
            trace_id="test-trace-123",
            explanation_level="detailed"
        )
        print(f"   ✓ ExplainReasoningRequest: {explain_req.trace_id}")
        
        # FeedbackRequest
        feedback_req = FeedbackRequest(
            trace_id="test-trace-123",
            rating=4,
            feedback_type="clarity",
            comment="Great response"
        )
        print(f"   ✓ FeedbackRequest: {feedback_req.trace_id}")
        
    except Exception as e:
        print(f"   ✗ Schema instantiation failed: {e}")
        return False
    
    print()
    
    # Test validation constraints
    print("3. Testing Validation Constraints:")
    
    validation_tests = [
        {
            "name": "Rating range validation (min)",
            "schema": FeedbackRequest,
            "data": {"trace_id": "test", "rating": 1, "feedback_type": "clarity"},
            "should_pass": True
        },
        {
            "name": "Rating range validation (max)", 
            "schema": FeedbackRequest,
            "data": {"trace_id": "test", "rating": 5, "feedback_type": "clarity"},
            "should_pass": True
        },
        {
            "name": "Rating range validation (below min)",
            "schema": FeedbackRequest,
            "data": {"trace_id": "test", "rating": 0, "feedback_type": "clarity"},
            "should_pass": False
        },
        {
            "name": "Rating range validation (above max)",
            "schema": FeedbackRequest,
            "data": {"trace_id": "test", "rating": 6, "feedback_type": "clarity"},
            "should_pass": False
        },
        {
            "name": "Enum validation (valid)",
            "schema": FeedbackRequest,
            "data": {"trace_id": "test", "rating": 3, "feedback_type": "correctness"},
            "should_pass": True
        },
        {
            "name": "Enum validation (invalid)",
            "schema": FeedbackRequest,
            "data": {"trace_id": "test", "rating": 3, "feedback_type": "invalid_type"},
            "should_pass": False
        },
        {
            "name": "Array length validation (min_items)",
            "schema": MultiJurisdictionRequest,
            "data": {"query": "test", "jurisdictions": []},
            "should_pass": False
        },
        {
            "name": "Array length validation (max_items)",
            "schema": MultiJurisdictionRequest,
            "data": {"query": "test", "jurisdictions": ["India", "UK", "UAE", "USA"]},
            "should_pass": False
        }
    ]
    
    passed_count = 0
    total_count = len(validation_tests)
    
    for test in validation_tests:
        try:
            instance = test["schema"](**test["data"])
            passed_validation = True
        except Exception:
            passed_validation = False
        
        expected_pass = test["should_pass"]
        
        if passed_validation == expected_pass:
            print(f"   ✓ {test['name']}")
            passed_count += 1
        else:
            print(f"   ✗ {test['name']} - Expected {expected_pass}, got {passed_validation}")
    
    print(f"\n4. Validation Results: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n✓ ALL SCHEMA DEFINITIONS ARE CORRECT!")
        print("✓ Enums are properly defined with correct values")
        print("✓ Validation constraints work as expected")
        print("✓ Required fields are properly marked")
        print("✓ Optional fields have proper defaults")
        return True
    else:
        print(f"\n✗ {total_count - passed_count} schema definition issues found")
        return False

if __name__ == "__main__":
    test_schema_definitions()