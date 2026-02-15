declare module "rcon" {
  export default class Rcon {
    constructor(host: string, port: number, password: string);
    on(event: string, callback: (err?: any) => void): void;
    connect(): Promise<void>;
    send(command: string): Promise<string>;
    disconnect(): void;
  }
}
