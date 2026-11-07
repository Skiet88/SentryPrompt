import { MIN_PASSWORD_LENGTH } from "./authMessages";

const EMAIL = /^[^\s@]{1,64}@[^\s@]{1,253}\.[^\s@.]{2,24}$/;

export function emailError(email: string): string | undefined {
  if (!email.trim()) return "Enter your email address.";
  if (email.trim().length > 254 || !EMAIL.test(email.trim())) return "Enter a valid email address, like name@uni.ac.za.";
  return undefined;
}

export function newPasswordError(password: string): string | undefined {
  if (password.length < MIN_PASSWORD_LENGTH) return `Use at least ${MIN_PASSWORD_LENGTH} characters.`;
  if (password.length > 72) return "Use at most 72 characters.";
  if (!/[a-zA-Z]/.test(password) || !/\d/.test(password)) return "Mix letters and numbers.";
  return undefined;
}
