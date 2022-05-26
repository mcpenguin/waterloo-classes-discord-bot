// load env var from .env
import 'dotenv/config'

import express, { Express } from "express"
import mongoose from "mongoose"
import cors from "cors"
import jobRoutes from "./routes"

const app: Express = express()

const PORT: string | number = process.env.PORT || 5000

app.use(cors())
app.use(jobRoutes)

const uri: string = process.env.ATLAS_URI ?? ""
const options = { useNewUrlParser: true, useUnifiedTopology: true }

// mongoose.set("useFindAndModify", false)

if (uri !== "") {
    mongoose
        .connect(uri, options)
        .then(() =>
            app.listen(PORT, () =>
                console.log(`Server running on http://localhost:${PORT}`)
            )
        )
        .catch(error => {
            throw error
        })
}
else {
    console.log("Invalid URI");
}
