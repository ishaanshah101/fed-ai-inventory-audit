# Rater instruction

You are one of six independent raters in a content-analysis study. You will read short
descriptions of AI systems and record judgements against a fixed rubric. You have no
other context about the study and you must not infer or guess who operates each system.
Rate each item on what its text says, nothing else.

## Input and output

Read `INPUT_PATH`, a JSON list of items. Each item has `rid` (an integer) and these
text fields, some of which may be empty: `use_case_name`, `topic_area`,
`classification`, `problem_solved`, `benefits`, `system_outputs`, `data_description`.
Organisation names in the text have been replaced with `[agency]`.

Write one JSON object per line to `OUTPUT_PATH`, one line per item, in the order given,
with exactly these keys:

```json
{"rater": R, "rid": 17, "category": "m", "decision_role": "assistive",
 "quantified": false, "metric_named": false, "evaluation_described": false,
 "baseline_given": false, "uncertainty_given": false, "stage": "in_use"}
```

`rater` is the integer `R` you were given. Every item must have a line. Do not skip,
merge or reorder. Do not add keys. Do not write anything else to the file.

## Part A: high-impact reading

The following definition and category list are reproduced verbatim from OMB
Memorandum M-25-21. Apply them to the description as written.

> **High-Impact AI:** AI with an output that serves as a principal basis for decisions
> or actions with legal, material, binding, or significant effect on: (1) an individual
> or entity's civil rights, civil liberties, or privacy; (2) an individual or entity's
> access to education, housing, insurance, credit, employment, and other programs;
> (3) an individual or entity's access to critical government resources or services;
> (4) human health and safety; (5) critical infrastructure or public safety; or
> (6) strategic assets or resources, including high-value property and information
> marked as sensitive or classified by the Federal Government.

**`category`**: the single letter of the presumption category below that the described
use most closely falls into, or the string `"none"` if it falls into none of them.
Choose the closest one; if two apply, choose the one the description emphasises.

> a. Safety-critical functions of critical infrastructure or government facilities,
> emergency services, fire and life safety systems within structures, food safety
> mechanisms, or traffic control systems and other systems controlling physical transit;
> b. Physical movements of robots, robotic appendages, vehicles or craft (whether land,
> sea, air, or underground), or industrial equipment that have the potential to cause
> significant injury to humans;
> c. Use of kinetic or non-kinetic measures for attack or active defense in real world
> circumstances that could cause significant injury to humans;
> d. Transport, safety, design, development, or use of hazardous chemicals or
> biological agents;
> e. Design, construction, or testing of equipment, systems, or public infrastructure
> that would pose a significant risk to safety if they failed;
> f. In healthcare contexts, the medically relevant functions of medical devices;
> patient diagnosis, risk assessment, or treatment; the allocation of care in the
> context of public insurance; or the control of health-insurance costs and
> underwriting;
> g. Control of access to, or the security of, government facilities;
> h. Adjudication or enforcement of sanctions, trade restrictions, or other controls on
> exports, investments, or shipping;
> i. The blocking, removal, hiding, or limitation of the reach of protected speech;
> j. In law enforcement contexts, production of risk assessments about individuals;
> identification of criminal suspects; forecast of crime; tracking of non-governmental
> vehicles over time in public spaces; application of biometric identification (e.g.,
> iris, facial, fingerprint, or gait matching); facial reconstruction based on genetic
> information; social media monitoring; application of digital forensic techniques; use
> of cyber intrusions; physical location-monitoring or tracking of individuals;
> detection of weapons or violent activity; or determinations related to recidivism,
> sentencing, parole, supervised release, probation, bail, pretrial release, or
> pretrial detention;
> k. Preparation or adjudication of risk assessments related to foreign nationals
> seeking temporary or permanent access to the U.S. or its territories including
> related to immigration, asylum, detention, or travel approval status;
> l. Use of biometric identification for one-to-many identification in publicly
> accessible spaces;
> m. Ability to apply for, or adjudication of, requests for critical federal services,
> processes, and benefits to include loans and access to public housing; determination
> of continued eligibility for ongoing benefits; the control of access, through
> biometrics or other means (e.g., signature matching), to IT systems for accessing
> services for benefits; detection of fraudulent use or attempted use of government
> services; adjudication of penalties in the context of government benefits;
> n. Determination of the terms or conditions of Federal employment, including
> pre-employment screening, reasonable accommodation, pay or promotion, performance
> management, hiring or termination, or recommending disciplinary action; reassignment
> of workers to new tasks or teams; or
> o. Provision of language translation (e.g., foreign translation and audiovisual
> translation) when responses are legally binding or for an interaction that directly
> informs an agency decision or action.

A use case falls into a category only if the AI is doing the thing the category
describes. Internal document search for staff, IT log analysis, code assistants,
research modelling, scientific data processing, chatbots that answer general questions,
and summarisation for employees fall into no category unless the text says the output
feeds one of the listed decisions or actions.

**`decision_role`**: exactly one of

- `"principal"`: the text describes the AI output as determining, deciding, approving,
  denying, or being the main basis for a decision or action about a person, a benefit,
  an enforcement outcome, or physical safety.
- `"assistive"`: the text describes the AI output as informing, flagging, prioritising,
  ranking, drafting, recommending, or otherwise supporting a human who makes that
  decision or takes that action.
- `"none"`: the text describes no decision or action about individuals, benefits,
  enforcement, or safety at all. Efficiency, search, summarisation, analytics for
  internal reporting, and research all fall here.

Record `decision_role` independently of `category`: a use can have a category and
`decision_role` of `"none"` if the text describes, say, statistical research in a
healthcare context that feeds no decision.

## Part B: evidence of performance

Five judgements, each `true` or `false`, applied to all the text shown for the item.

1. `quantified`: a specific numeric performance figure is attributed to the AI
   (an accuracy, an error rate, a percentage of time saved, a throughput, a cost
   reduction with a number). A count of users, a budget, a date, a year, a document
   count in the training set, or a number of records processed is not a performance
   figure.
2. `metric_named`: the quantity being claimed is named (accuracy, precision, recall,
   false positive rate, processing time, hours saved, cost per case, backlog reduced),
   whether or not a number is attached.
3. `evaluation_described`: the text says what data, population, or period a
   performance figure was measured over.
4. `baseline_given`: the text says what a performance figure is compared against
   (a prior process, a manual baseline, a previous model, a prior period).
5. `uncertainty_given`: an interval, a sample size for the evaluation, or any error
   estimate is stated.

If `quantified` is false, `evaluation_described`, `baseline_given` and
`uncertainty_given` will almost always be false too, but judge each on its own.

## Part C: stage reading

`stage`: exactly one of

- `"in_use"`: the text describes the system as currently operating, in production, in
  use by staff or the public, or having produced results.
- `"not_yet"`: the text describes the system as being developed, planned, proposed,
  under evaluation, being piloted, or expected to do things in future.
- `"unclear"`: the text does not let you tell.

Present-tense descriptions of capability ("the model classifies images") without any
indication of operational status are `"unclear"`, not `"in_use"`.

## Conduct

Work through every item. Do not look up anything. Do not read any other file. If a
field is empty, rate on what remains. When you finish, report only the count of lines
written and the count per `category` value and per `decision_role` value.
