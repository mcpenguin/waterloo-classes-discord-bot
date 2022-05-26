import { Router } from "express"
import { getJobs, addJob, updateJob, deleteJob } from "../controllers/jobs"

const router: Router = Router()

// make routes
router.get("/jobs", getJobs)
router.post("/add-job", addJob)
router.put("/edit-job/:id", updateJob)
router.delete("/delete-job/:id", deleteJob)

export default router
