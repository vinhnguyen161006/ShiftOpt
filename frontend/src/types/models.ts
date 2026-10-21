import type { components } from "./api";

type Schemas = components["schemas"];

export type DemandProfileRead = Schemas["DemandProfileRead"];
export type DemandProfileCreate = Schemas["DemandProfileCreate"];
export type DemandProfileUpdate = Schemas["DemandProfileUpdate"];
export type DatasetDemandRequest = Schemas["DatasetDemandRequest"];
export type EmployeeRead = Schemas["EmployeeRead"];
export type EmployeeCreate = Schemas["EmployeeCreate"];
export type ShiftTemplateRead = Schemas["ShiftTemplateRead"];
export type ShiftTemplateCreate = Schemas["ShiftTemplateCreate"];
export type SolveRequest = Schemas["SolveRequest"];
export type JobAccepted = Schemas["JobAccepted"];
export type SolveRunRead = Schemas["SolveRunRead"];
export type ComplianceRead = Schemas["ComplianceRead"];
export type KpiRead = Schemas["KpiRead"];
export type DemandSweepRequest = Schemas["DemandSweepRequest"];
export type AnalysisAccepted = Schemas["AnalysisAccepted"];
export type AnalysisRunRead = Schemas["AnalysisRunRead"];
