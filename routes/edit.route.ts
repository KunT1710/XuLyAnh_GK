import { Router } from "express";

const router : Router = Router();

import * as controller from "../controllers/edit.controller";

router.get("/", controller.edit);

export const exditRoutes: Router = router;