const clamp = value => Math.max(0, Math.min(1, value));
export const REVEAL_SECONDS = 1.6;
export function revealValue(score, age) {
  const t = clamp(age / .7);
  return Math.round(score * (1 - (1-t)**3));
}
export function giftMotion(age) {
  const opacity = Math.min(clamp(age / .14), clamp((1.8-age) / .35));
  const pulse = age < .8 ? Math.sin(age * Math.PI * 5) * .045 : 0;
  return {opacity, scale: .94 + .06 * clamp(age / .2) + pulse, rise: clamp(age / 1.8)};
}
export class PresentationState {
  constructor() { this.enabled = true; this.cancel(); }
  begin(job) {
    this.cancel();
    this.job = job;
    this.hasGift = !!(job.gift || job.priority) && (job.copy || 1) === 1;
  }
  complete(score) { this.finalScore = score; this.resultAge = 0; }
  tick(dt, paused = false) {
    if (paused || !Number.isFinite(dt) || dt < 0) return;
    this.giftAge += dt;
    if (this.resultAge !== null) this.resultAge += dt;
  }
  get giftVisible() { return this.enabled && this.hasGift && this.giftAge < 1.8; }
  get score() { return this.resultAge === null ? null : this.enabled ? revealValue(this.finalScore, this.resultAge) : this.finalScore; }
  get revealDone() { return !this.enabled || (this.resultAge !== null && this.resultAge >= REVEAL_SECONDS); }
  cancel() { this.job = null; this.hasGift = false; this.giftAge = 0; this.resultAge = null; this.finalScore = null; }
}
