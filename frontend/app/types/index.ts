export interface LoginPayload { username: string; password: string }
export interface UserInfo { username: string }
export interface InstanceData { id: string; name: string; port: number; status: string; jar_name?: string; selected_core?: string; created_at?: number }
export interface DeployWizardData { mode: 'quick' | 'bedrock' | 'package' | 'mcdr' | ''; name: string; port: number; coreType: string; mcVersion: string; buildVersion: string; javaVersion: string; memory: number; useAikar: boolean; packageFile: File | null; packageInfo?: unknown }
