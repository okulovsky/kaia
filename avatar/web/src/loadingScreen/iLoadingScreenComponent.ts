export interface ILoadingScreenComponent {
    readonly name: string
    initialize(): Promise<void>
}
