/**
 * Re-export DisclaimerStrip as DisclaimerBanner for existing imports/tests.
 * See PLAN.md Section 12 and TASKS.md T45.
 */
export {
  default,
  DEFAULT_CONSENT_TO_LOG,
  type DisclaimerStripProps as DisclaimerBannerProps,
} from "@/components/layout/DisclaimerStrip";
