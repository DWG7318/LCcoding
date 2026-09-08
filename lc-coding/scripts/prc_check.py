#!/usr/bin/env python3
from pathlib import Path
import argparse, json

REQUIRED = ['problem','target_users','core_value','scope','constraints','success_criteria']
FIT_FACTS = {
    'human_beneficiary': (
        'Confirm the identifiable human beneficiary or authorized representative.',
        'Record true or false and cite the proposal evidence for the beneficiary.',
    ),
    'complete_journey': (
        'Confirm a complete product or service journey from intent to observable outcome.',
        'Record true or false and summarize the promised end-to-end journey.',
    ),
    'real_workflow': (
        'Confirm real business Workflow with actors, rules, state changes, effects, and recovery.',
        'Record true or false and identify the material Workflow behavior.',
    ),
    'actor_facing_surface': (
        'Confirm an actor-facing UI, result, Agent-service, CLI, or assisted-service surface.',
        'Record true or false and name the actual product surface.',
    ),
    'integration_need': (
        'Confirm a need to integrate the surface, Workflow, Simulation, and Backend/Core.',
        'Record true or false and identify the delivered integration boundary.',
    ),
    'real_acceptance_entry': (
        'Confirm a feasible real-journey acceptance path from a promised entry point.',
        'Record true or false and name the real acceptance entry and observable outcome.',
    ),
}
BOUNDED_SCOPE = 'bounded_product_scope'


def fit_questions(data):
    fit = data.get('lccoding_fit')
    if not isinstance(fit, dict):
        fit = {}
    missing = []
    questions = []
    for field, (question, recommended_answer) in FIT_FACTS.items():
        if type(fit.get(field)) is not bool:
            qualified = 'lccoding_fit.' + field
            missing.append(qualified)
            questions.append({
                'field': qualified,
                'question': question,
                'recommended_answer': recommended_answer,
            })
    if type(fit.get(BOUNDED_SCOPE)) is not bool:
        qualified = 'lccoding_fit.' + BOUNDED_SCOPE
        missing.append(qualified)
        questions.append({
            'field': qualified,
            'question': 'Confirm whether LCCoding should cover only a complete bounded product-facing scope.',
            'recommended_answer': 'Set true only for an explicitly bounded complete product journey; otherwise set false.',
        })
    return fit, missing, questions


def conflict_questions(conflicts):
    if not conflicts:
        return []
    items = conflicts if isinstance(conflicts, list) else [conflicts]
    questions = []
    for index, conflict in enumerate(items):
        if isinstance(conflict, dict):
            summary = conflict.get('topic') or conflict.get('field') or 'the recorded proposal conflict'
        elif isinstance(conflict, str) and conflict.strip():
            summary = conflict.strip()
        else:
            summary = 'the recorded proposal conflict'
        questions.append({
            'field': f'conflicts[{index}]',
            'question': f'Which authoritative decision resolves this conflict: {summary}?',
            'recommended_answer': 'Choose one authoritative interpretation and update the proposal evidence to match it.',
        })
    return questions


def assess_applicability(data, missing, conflicts):
    fit, fit_missing, fit_question_rows = fit_questions(data)
    missing.extend(fit_missing)
    if missing or conflicts:
        reasons = []
        if missing:
            reasons.append('No applicability outcome is issued until the missing or invalid facts are resolved.')
        if conflicts:
            reasons.append('No applicability outcome is issued while proposal conflicts remain unresolved.')
        return None, reasons, fit_question_rows

    absent_facts = [field for field in FIT_FACTS if fit[field] is False]
    if absent_facts:
        labels = ', '.join(field.replace('_', ' ') for field in absent_facts)
        return (
            'OTHER_METHOD_RECOMMENDED',
            [
                'Complete evidence shows that the full LCCoding lifecycle does not fit this engineering object.',
                'Absent product-fit facts: ' + labels + '.',
                'This recommends another method for the assessed scope; it does not reject the underlying project.',
                'Use a component-focused engineering and verification approach for library, algorithm, infrastructure, or other non-product work.',
            ],
            fit_question_rows,
        )
    if fit[BOUNDED_SCOPE]:
        return (
            'BOUNDED_PRODUCT_FIT',
            [
                'All six LCCoding product-fit facts are present.',
                'Apply LCCoding only to the identified complete bounded product-facing scope.',
            ],
            fit_question_rows,
        )
    return (
        'WHOLE_PRODUCT_FIT',
        [
            'All six LCCoding product-fit facts are present.',
            'The proposed whole-product scope is suitable for the full LCCoding lifecycle.',
        ],
        fit_question_rows,
    )

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('proposal_json')
    args=ap.parse_args()
    data=json.loads(Path(args.proposal_json).read_text(encoding='utf-8'))
    missing=[k for k in REQUIRED if not data.get(k)]
    conflicts=data.get('conflicts',[])
    recommendation, reasons, fit_question_rows = assess_applicability(data, missing, conflicts)
    result={'status':'PROPOSAL_READY' if not missing and not conflicts else 'PROPOSAL_INCOMPLETE',
            'missing_blockers':missing,'conflicts':conflicts,
            'questions':[{'field':k,'question':f'Please resolve {k}.','recommended_answer':''} for k in missing if not k.startswith('lccoding_fit.')] + fit_question_rows + conflict_questions(conflicts),
            'applicability_recommendation':recommendation,
            'applicability_reasons':reasons,
            'service_strategy_discussion_required':recommendation in {'WHOLE_PRODUCT_FIT','BOUNDED_PRODUCT_FIT'}}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
