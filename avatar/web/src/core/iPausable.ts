export interface IPausable {
  pause(): Promise<void> | void
  resume(): Promise<void> | void
}
