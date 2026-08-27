declare module "three";

declare module "three/addons/loaders/GLTFLoader.js" {
  export class GLTFLoader {
    register(...args: any[]): void;
    load(...args: any[]): void;
  }
}

declare module "three/examples/jsm/loaders/GLTFLoader.js" {
  export class GLTFLoader {
    register(...args: any[]): void;
    load(...args: any[]): void;
  }
}