/** Short, plain names for the detection categories (backend detection_categories.json). */
const LABELS: Record<string, string> = {
  SA_ID: "ID number",
  BANK_CARD: "Card number",
  BANK_ACCOUNT: "Account number",
  PHONE: "Phone number",
  EMAIL: "Email address",
  ADDRESS: "Street address",
  STUDENT_NUMBER: "Student number",
  MEDICAL: "Health information",
  INSTITUTIONAL: "Confidential university information",
};

export function categoryLabel(category: string): string {
  const known = LABELS[category.toUpperCase()];
  if (known) return known;
  const words = category.toLowerCase().replace(/_/g, " ").trim();
  return words ? words.charAt(0).toUpperCase() + words.slice(1) : "Sensitive information";
}
