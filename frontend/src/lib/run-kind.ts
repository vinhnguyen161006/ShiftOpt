export function isRepairRun(run: { repair_from_day?: number | null }): boolean {
  return run.repair_from_day !== null && run.repair_from_day !== undefined;
}
