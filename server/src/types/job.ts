import { Document } from "mongoose";

export interface IJob extends Document {
    name: string,
    company: string,
    // can add more fields later
}
