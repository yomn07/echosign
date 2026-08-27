import axios from "axios";

const API_URL = "";

export type TrialStatus = {
  trial_id?: string;
  trials_remaining?: number | null;
  trial_used?: boolean;
  requires_login?: boolean;
  authenticated?: boolean;
  user?: {
    id: number;
    first_name: string;
    last_name: string;
    email: string;
    role?: string;
    is_verified?: boolean;
  };
};

export async function getTrialStatus(): Promise<TrialStatus> {
  const token =
    sessionStorage.getItem("access_token");

  const response = await axios.get(
    `${API_URL}/trial/status`,
    {
      withCredentials: true,

      headers: token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : undefined,
    }
  );

  return response.data;
}