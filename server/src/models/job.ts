import { IJob } from "../types/job"
import { model, Schema } from "mongoose"

const jobSchema: Schema = new Schema(
    {
        name: {
            type: String,
            required: true,
        },

        company: {
            type: String,
            required: true,
        },
    },
    { timestamps: true }
)

export default model<IJob>("Job", jobSchema)
