export const caseTasks = [
  ["artery_and_stenosis", "Artery and stenosis research"],
  ["artery_segmentation", "Artery segmentation"],
  ["stenosis_localization", "Stenosis localization"],
  ["volume_preparation", "3D volume workflow"],
] as const;
export const caseAnatomies = ["coronary", "aorta", "cerebral", "hepatic"];
export function taskLabel(task?: string) {
  return caseTasks.find(([id]) => id === task)?.[1] || "Legacy research configuration";
}
