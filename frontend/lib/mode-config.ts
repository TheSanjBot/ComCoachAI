export const MODE_CONFIG = {
  "interview-training": {
    title: "Interview Training Mode",
    shortTitle: "Interview training",
    supportsRecording: true,
    studioTitle: "Record an interview answer",
    studioDescription:
      "Run a structured mock interview with role-based questions, answer by video, and then layer technical evaluation on top of the staged analysis pipeline.",
    launchLabel: "Open interview workspace",
    checklist: [
      "Keep your face centered and shoulders visible.",
      "Answer one focused prompt at a time.",
      "Use the live timer to stay concise under pressure."
    ]
  },
  "public-speaking": {
    title: "Public Speaking Training Mode",
    shortTitle: "Public speaking",
    supportsRecording: true,
    studioTitle: "Record a speaking rehearsal",
    studioDescription:
      "Practice a focused rehearsal, then convert the analyzed recording into pacing, posture, eye-contact, and communication coaching.",
    launchLabel: "Open speaking workspace",
    checklist: [
      "Frame yourself from the chest upward when possible.",
      "Speak naturally instead of over-correcting during the take.",
      "Use one clear topic or opening story for this recording."
    ]
  },
  "resume-skill-gap": {
    title: "Resume + Skill Gap Analysis Mode",
    shortTitle: "Resume analysis",
    supportsRecording: false,
    studioTitle: "Upload and analyze your resume",
    studioDescription:
      "Upload a PDF or TXT resume, compare it against a target role, and generate missing-skill insights plus a learning roadmap.",
    launchLabel: "Open resume workspace",
    checklist: [
      "Upload a PDF or TXT resume for parsing.",
      "Choose the target role you want to benchmark against.",
      "Review missing skills, recommendations, and personalized coaching."
    ]
  }
} as const;

export type ModeSlug = keyof typeof MODE_CONFIG;
export type RecordingModeSlug = {
  [K in ModeSlug]: (typeof MODE_CONFIG)[K]["supportsRecording"] extends true ? K : never;
}[ModeSlug];

export function isModeSlug(value: string | null): value is ModeSlug {
  return value !== null && value in MODE_CONFIG;
}

export function isRecordingModeSlug(value: ModeSlug): value is RecordingModeSlug {
  return MODE_CONFIG[value].supportsRecording;
}

export function getModeConfig(mode: ModeSlug) {
  return MODE_CONFIG[mode];
}

export function getStudioHref(mode: RecordingModeSlug) {
  return `/studio?mode=${encodeURIComponent(mode)}`;
}

export function getModeHref(mode: ModeSlug) {
  if (isRecordingModeSlug(mode)) {
    return getStudioHref(mode);
  }
  return "/resume-analysis";
}
