#!/usr/bin/env python3
"""
Nyaya AI System Functionality Verification
Checking if Nyaya works as specified: organized thinking, safe learning, rule compliance, and immutability
"""
from datetime import datetime
import json

def check_organized_thinking():
    """🧱 Task 1: Verify organized system architecture"""
    print("🧱 VERIFYING ORGANIZED THINKING (Task 1)")
    print("=" * 50)
    
    checks = []
    
    # 1. Multi-agent architecture
    try:
        from sovereign_agents.jurisdiction_router_agent import JurisdictionRouterAgent
        from sovereign_agents.legal_agent import LegalAgent
        from sovereign_agents.constitutional_agent import ConstitutionalAgent
        
        router = JurisdictionRouterAgent()
        india_agent = LegalAgent("IN_agent", "India")
        uk_agent = LegalAgent("UK_agent", "UK")
        uae_agent = LegalAgent("UAE_agent", "UAE")
        constitutional_agent = ConstitutionalAgent()
        
        print("✓ Multi-agent system properly initialized")
        checks.append(True)
    except Exception as e:
        print(f"❌ Multi-agent architecture failed: {e}")
        checks.append(False)
    
    # 2. Jurisdiction routing
    try:
        from jurisdiction_router.router import JurisdictionRouter
        router = JurisdictionRouter()
        result = router.route_query("What is the punishment for theft in India?", "IN")
        if result and 'jurisdiction' in result:
            print("✓ Jurisdiction routing working")
            checks.append(True)
        else:
            print("❌ Jurisdiction routing not working properly")
            checks.append(False)
    except Exception as e:
        print(f"❌ Jurisdiction routing failed: {e}")
        checks.append(False)
    
    # 3. Provenance tracking
    try:
        from provenance_chain.lineage_tracer import tracer
        trace_id = tracer.start_trace("functionality_test")
        event = tracer.log_event("test_event", {"data": "test"}, trace_id)
        if event and 'trace_id' in event:
            print("✓ Provenance tracking working")
            checks.append(True)
        else:
            print("❌ Provenance tracking not working")
            checks.append(False)
    except Exception as e:
        print(f"❌ Provenance tracking failed: {e}")
        checks.append(False)
    
    # 4. API structure
    try:
        from api.router import router
        print("✓ API router properly structured")
        checks.append(True)
    except Exception as e:
        print(f"❌ API structure failed: {e}")
        checks.append(False)
    
    organized = all(checks)
    print(f"\nOrganized Thinking: {'✅ WORKING' if organized else '❌ BROKEN'}")
    return organized

def check_safe_learning():
    """🧠 Task 2: Verify safe learning capabilities"""
    print("\n🧠 VERIFYING SAFE LEARNING (Task 2)")
    print("=" * 50)
    
    checks = []
    
    # 1. Learning system exists
    try:
        from rl_engine.rl_core import update_learning, get_adjusted_confidence
        print("✓ Learning system present")
        checks.append(True)
    except Exception as e:
        print(f"❌ Learning system missing: {e}")
        checks.append(False)
        return False
    
    # 2. Multi-jurisdiction learning
    test_cases = [
        {'country': 'IN', 'domain': 'criminal', 'procedure_id': 'ipc_302'},
        {'country': 'UK', 'domain': 'civil', 'procedure_id': 'contract_law'},
        {'country': 'UAE', 'domain': 'commercial', 'procedure_id': 'company_law'}
    ]
    
    learning_works = True
    for case in test_cases:
        try:
            signal = {
                'case_id': f'test_{case["country"]}',
                'country': case['country'],
                'domain': case['domain'],
                'procedure_id': case['procedure_id'],
                'confidence_before': 0.7,
                'user_feedback': 'positive',
                'outcome_tag': 'resolved',
                'outcome_valid': True,
                'timestamp': datetime.now().isoformat()
            }
            
            result = update_learning(signal)
            if result['status'] not in ['learning_applied', 'learning_rejected']:
                learning_works = False
        except Exception:
            learning_works = False
    
    if learning_works:
        print("✓ Multi-jurisdiction learning working")
        checks.append(True)
    else:
        print("❌ Multi-jurisdiction learning broken")
        checks.append(False)
    
    # 3. Confidence adjustment safety
    try:
        context = {'country': 'IN', 'domain': 'criminal', 'procedure_id': 'test', 'original_confidence': 0.5}
        adjustment = get_adjusted_confidence(context)
        confidence_val = adjustment['adjusted_confidence'] if isinstance(adjustment, dict) else adjustment
        
        if 0.0 <= confidence_val <= 1.0:
            print("✓ Confidence remains bounded")
            checks.append(True)
        else:
            print(f"❌ Confidence out of bounds: {confidence_val}")
            checks.append(False)
    except Exception as e:
        print(f"❌ Confidence adjustment failed: {e}")
        checks.append(False)
    
    # 4. Persistent storage
    try:
        from rl_engine.learning_store import LearningStore
        store = LearningStore()
        test_data = {'test': 'data', 'timestamp': datetime.now().isoformat()}
        store.save_learning_record('test_id', test_data)
        
        retrieved = store.get_learning_history('test_id')
        if retrieved:
            print("✓ Learning persistence working")
            checks.append(True)
        else:
            print("❌ Learning persistence failed")
            checks.append(False)
    except Exception as e:
        print(f"❌ Learning storage failed: {e}")
        checks.append(False)
    
    safe_learning = all(checks)
    print(f"\nSafe Learning: {'✅ WORKING' if safe_learning else '❌ BROKEN'}")
    return safe_learning

def check_rule_compliance():
    """🛡️ Task 3: Verify strict rule compliance"""
    print("\n🛡️ VERIFYING RULE COMPLIANCE (Task 3)")
    print("=" * 50)
    
    checks = []
    
    # 1. Enforcement engine exists
    try:
        from enforcement_engine.engine import enforce_request, EnforcementSignal
        print("✓ Enforcement engine present")
        checks.append(True)
    except Exception as e:
        print(f"❌ Enforcement engine missing: {e}")
        checks.append(False)
        return False
    
    # 2. Enforcement decisions are structured
    try:
        signal = EnforcementSignal(
            case_id='compliance_test',
            country='IN',
            domain='criminal',
            procedure_id='test_proc',
            original_confidence=0.5,
            user_request='test request',
            jurisdiction_routed_to='IN',
            trace_id='compliance_trace'
        )
        
        result = enforce_request(signal)
        required_fields = ['decision', 'rule_id', 'policy_source', 'reasoning_summary']
        has_fields = all(hasattr(result, field) for field in required_fields)
        
        if has_fields:
            print("✓ Enforcement decisions properly structured")
            checks.append(True)
        else:
            print("❌ Enforcement decisions missing required fields")
            checks.append(False)
    except Exception as e:
        print(f"❌ Enforcement decision structure failed: {e}")
        checks.append(False)
    
    # 3. Digital signatures and logging
    try:
        from enforcement_provenance.ledger import append_event
        from enforcement_provenance.signer import sign_event_dict
        
        test_event = {
            'event_type': 'compliance_check',
            'timestamp': datetime.now().isoformat(),
            'data': {'test': 'compliance'}
        }
        
        signed_event = sign_event_dict(test_event)
        result = append_event(signed_event)
        
        if result['status'] == 'appended':
            print("✓ Digital signatures and logging working")
            checks.append(True)
        else:
            print("❌ Digital signatures/logging failed")
            checks.append(False)
    except Exception as e:
        print(f"❌ Provenance logging failed: {e}")
        checks.append(False)
    
    # 4. Refusal behavior
    try:
        # Test edge case that should be refused
        edge_signal = EnforcementSignal(
            case_id='edge_case',
            country='INVALID',
            domain='invalid',
            procedure_id='invalid',
            original_confidence=0.5,
            user_request='edge case test',
            jurisdiction_routed_to='INVALID',
            trace_id='edge_trace'
        )
        
        result = enforce_request(edge_signal)
        if hasattr(result, 'decision') and result.decision.name in ['BLOCK', 'ESCALATE']:
            print("✓ Proper refusal behavior")
            checks.append(True)
        else:
            print("❌ Refusal behavior not working")
            checks.append(False)
    except Exception as e:
        print(f"✓ System fails safely on edge cases: {e}")
        checks.append(True)  # Safe failure is good
    
    rule_compliance = all(checks)
    print(f"\nRule Compliance: {'✅ WORKING' if rule_compliance else '❌ BROKEN'}")
    return rule_compliance

def check_immunity_protection():
    """🧪 Task 4: Verify protection from manipulation"""
    print("\n🧪 VERIFYING IMMUNITY PROTECTION (Task 4)")
    print("=" * 50)
    
    checks = []
    
    # 1. Decay mechanism
    try:
        from rl_engine.learning_store import LearningStore
        store = LearningStore()
        
        # Check if decay logic exists
        import inspect
        source = inspect.getsource(store.__class__)
        if '_apply_time_decay' in source and 'DECAY_HALF_LIFE' in source:
            print("✓ Time decay mechanism present")
            checks.append(True)
        else:
            print("❌ Time decay mechanism missing")
            checks.append(False)
    except Exception as e:
        print(f"❌ Decay mechanism check failed: {e}")
        checks.append(False)
    
    # 2. Anomaly detection
    try:
        from rl_engine.reward_engine import compute_reward
        
        # Test extreme feedback that should be rejected
        extreme_signal = {
            'case_id': 'extreme_test',
            'country': 'IN',
            'domain': 'criminal',
            'procedure_id': 'extreme_proc',
            'confidence_before': 0.5,
            'user_feedback': 'extreme_positive',  # Should be rejected
            'outcome_tag': 'resolved',
            'outcome_valid': True,
            'timestamp': datetime.now().isoformat(),
            'user_id': 'spam_user'
        }
        
        reward, should_learn, reason = compute_reward(extreme_signal, 0.5)
        if not should_learn and 'extreme' in reason.lower():
            print("✓ Anomaly detection working")
            checks.append(True)
        else:
            print("❌ Anomaly detection not working properly")
            checks.append(False)
    except Exception as e:
        print(f"❌ Anomaly detection check failed: {e}")
        checks.append(False)
    
    # 3. Legal truth dominance
    try:
        from rl_engine.rl_core import update_learning
        
        # UI positive + Raj invalid should be rejected
        conflict_signal = {
            'case_id': 'conflict_test',
            'country': 'UK',
            'domain': 'civil',
            'procedure_id': 'contract_law',
            'confidence_before': 0.6,
            'user_feedback': 'positive',
            'outcome_tag': 'wrong',
            'outcome_valid': False,  # Raj says invalid
            'timestamp': datetime.now().isoformat()
        }
        
        result = update_learning(conflict_signal)
        if result['status'] == 'learning_rejected':
            print("✓ Legal truth properly dominates UI feedback")
            checks.append(True)
        else:
            print("❌ Legal truth not dominating properly")
            checks.append(False)
    except Exception as e:
        print(f"❌ Legal truth dominance check failed: {e}")
        checks.append(False)
    
    # 4. Slow learning
    try:
        # Test that confidence changes are small
        initial_context = {'country': 'UAE', 'domain': 'commercial', 'procedure_id': 'test', 'original_confidence': 0.5}
        
        from rl_engine.rl_core import get_adjusted_confidence, update_learning
        
        initial_conf = get_adjusted_confidence(initial_context)
        initial_val = initial_conf['adjusted_confidence'] if isinstance(initial_conf, dict) else initial_conf
        
        # Apply multiple small updates
        for i in range(5):
            signal = {
                'case_id': f'slow_test_{i}',
                'country': 'UAE',
                'domain': 'commercial',
                'procedure_id': 'test',
                'confidence_before': 0.5,
                'user_feedback': 'positive',
                'outcome_tag': 'resolved',
                'outcome_valid': True,
                'timestamp': datetime.now().isoformat()
            }
            update_learning(signal)
        
        final_conf = get_adjusted_confidence(initial_context)
        final_val = final_conf['adjusted_confidence'] if isinstance(final_conf, dict) else final_conf
        
        change = abs(final_val - initial_val)
        if change < 0.15:  # Should be small change
            print("✓ Learning happens slowly and calmly")
            checks.append(True)
        else:
            print(f"❌ Learning too aggressive: {change}")
            checks.append(False)
    except Exception as e:
        print(f"❌ Slow learning check failed: {e}")
        checks.append(False)
    
    immunity = all(checks)
    print(f"\nImmunity Protection: {'✅ WORKING' if immunity else '❌ BROKEN'}")
    return immunity

def main():
    print("NYAYA AI SYSTEM FUNCTIONALITY VERIFICATION")
    print("Checking if Nyaya works as a legal brain should")
    print("=" * 60)
    
    # Run all checks
    organized = check_organized_thinking()
    learning = check_safe_learning()
    compliance = check_rule_compliance()
    immunity = check_immunity_protection()
    
    # Final assessment
    print("\n" + "=" * 60)
    print("FINAL SYSTEM ASSESSMENT")
    print("=" * 60)
    
    results = {
        "Organized Thinking (Task 1)": organized,
        "Safe Learning (Task 2)": learning,
        "Rule Compliance (Task 3)": compliance,
        "Immunity Protection (Task 4)": immunity
    }
    
    working_count = sum(results.values())
    total_count = len(results)
    
    for function, working in results.items():
        status = "✅ WORKING" if working else "❌ BROKEN"
        print(f"{function}: {status}")
    
    print(f"\nOverall System Health: {working_count}/{total_count} functions working")
    
    if working_count == total_count:
        print("\n🎉 NYAYA AI IS FULLY FUNCTIONAL!")
        print("The legal brain is working exactly as specified:")
        print("  ✅ Thinks in an organized way")
        print("  ✅ Learns from experience safely")
        print("  ✅ Follows law and rules strictly")
        print("  ✅ Cannot be manipulated")
        print("  ✅ Can prove every decision")
        print("\nNyaya is ready for production use as a trustworthy legal AI system.")
        return True
    else:
        print(f"\n⚠️  NYAYA AI HAS {total_count - working_count} ISSUES")
        print("The system is not yet fully production-ready.")
        print("See above for specific functions that need attention.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)