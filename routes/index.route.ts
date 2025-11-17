import { Express  } from "express";
import { homeRoutes } from "./home.route";
import { exditRoutes } from "./edit.route";

const Routes = (app :Express): void =>{
  
  app.use("/", homeRoutes);

  app.use("/edit", exditRoutes);
};

export default Routes;