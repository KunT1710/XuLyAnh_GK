import express, { Express } from "express";
import dotenv from "dotenv";
import * as database from "./config/database";
import Routes from "./routes/index.route";

dotenv.config();

const app: Express = express();
const port: string | number = process.env.PORT || 3000;

database.connect();

// Use PUG
app.set("views", "./views");
app.set("view engine", "pug");

app.use(express.static("public"));
// End Use PUG

// Routes
Routes(app);
// End Routes

app.listen(port, ()=>{
  console.log(`App listening on port ${port}`);
})