"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { Shield, Eye, EyeOff } from "lucide-react";
import { authApi } from "@/lib/api-client";
import { useAuthStore } from "@/lib/auth-store";

const schema = z.object({
  email: z.string().email("Email invalide"),
  password: z.string().min(1, "Mot de passe requis"),
});

type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setIsLoading(true);
    try {
      const res = await authApi.login(data);
      const { access_token, pseudo, user_id, role, level, total_xp } = res.data;
      const meRes = await authApi.me();
      login(access_token, meRes.data);
      toast.success(`Bon retour Agent ${pseudo} !`);
      router.replace("/dashboard");
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string; error?: string } } };
      const errorCode = error?.response?.data?.error;
      if (errorCode === "ACCOUNT_LOCKED") {
        toast.error("Trop de tentatives. Compte verrouillé 15 min.");
      } else {
        toast.error("Email ou mot de passe incorrect.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-cyber-bg flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Shield className="text-cyber-green" size={48} />
          </div>
          <h1 className="text-3xl font-bold text-cyber-green glow-green">CYBERLEARN</h1>
          <p className="text-cyber-muted mt-2">Accès agents CSDF</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="cyber-card space-y-4">
          <div>
            <label className="cyber-label">Email</label>
            <input {...register("email")} type="email" placeholder="agent@csdf.gov"
              className="cyber-input" autoFocus />
            {errors.email && <p className="cyber-error">{errors.email.message}</p>}
          </div>

          <div>
            <label className="cyber-label">Mot de passe</label>
            <div className="relative">
              <input {...register("password")} type={showPassword ? "text" : "password"}
                placeholder="••••••••" className="cyber-input pr-10" />
              <button type="button" onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-cyber-muted hover:text-cyber-text">
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            {errors.password && <p className="cyber-error">{errors.password.message}</p>}
          </div>

          <button type="submit" disabled={isLoading} className="cyber-btn-primary w-full">
            {isLoading ? "Connexion..." : "Se connecter →"}
          </button>

          <p className="text-center text-cyber-muted text-sm">
            Pas encore de compte ?{" "}
            <Link href="/register" className="text-cyber-cyan hover:underline">S'inscrire (18+)</Link>
          </p>
        </form>

        <p className="text-center text-cyber-muted text-xs mt-6">
          🔒 Ce jeu est réservé aux personnes de 18 ans et plus (PEGI 18+)
        </p>
      </div>
    </div>
  );
}
