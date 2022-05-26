import { Response, Request } from "express"
import { IJob } from "../../types/job"
import Job from "../../models/job"

// get list of jobs
export const getJobs = async (req: Request, res: Response): Promise<void> => {
    try {
        const todos: IJob[] = await Job.find()
        res.status(200).json({ todos })
    } catch (error) {
        throw error
    }
}

// add a job
export const addJob = async (req: Request, res: Response): Promise<void> => {
    try {
        const body = req.body as Pick<IJob, "name" | "company">

        const job: IJob = new Job({
            name: body.name,
            description: body.company,
        })

        const newJob: IJob = await job.save()
        const allJobs: IJob[] = await Job.find()

        res
            .status(201)
            .json({ message: "Todo added", todo: newJob, todos: allJobs })
    } catch (error) {
        throw error
    }
}

// update a job
export const updateJob = async (req: Request, res: Response): Promise<void> => {
    try {
        // get id from the request (ie id of the item we wish to update)
        const {
            params: { id },
            body,
        } = req

        // update the job with the id from the request
        const updateJob: IJob | null = await Job.findByIdAndUpdate(
            { _id: id },
            body
        )

        res.status(200).json({
            message: "Job updated",
            job: updateJob,
        })
    } catch (error) {
        throw error
    }
}

// delete a job
export const deleteJob = async (req: Request, res: Response): Promise<void> => {
    try {
        const deletedJob: IJob | null = await Job.findByIdAndRemove(
            req.params.id
        )
        const allJobs: IJob[] = await Job.find()
        res.status(200).json({
            message: "Job deleted",
            todo: deletedJob,
            todos: allJobs,
        })
    } catch (error) {
        throw error
    }
}

