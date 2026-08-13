# Protected Delivery Guidance

`SPEC.md` defines Delivery; Delivery evidence is not a security verdict.

<a id="decision-before-delivery"></a>
## Decision before delivery

Source clauses: [LC-DELIVERY-001](../../SPEC.md#lc-delivery-001)

After current Post-Security acceptance, complete Delivery Method Q&A and persist decisions. Actual Delivery starts only after `DELIVERY_READY`; Q&A is not actual Delivery. See [Delivery Method Q&A](delivery-method-qa.md).

<a id="protected-package"></a>
## Protected package

Source clauses: [LC-DELIVERY-001](../../SPEC.md#lc-delivery-001)

Deliver approved product and customer assets with default internal exclusions. Source code requires explicit Owner authorization; Owner Policy hard constraints are not customer options. Ubuntu and no-source are recommendations. Legal limits must not be invented from silence.

package evidence and guard bind the current candidate and asset integrity. Re-check packaging effects; it does not repeat unchanged product verification. Fields stay in the Decision, Manifest, and guard.
