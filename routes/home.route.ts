import { Router } from "express";

const router : Router = Router();

import * as controller from "../controllers/home.controller";

router.get("/", controller.home);

export const homeRoutes: Router = router;