import { Component, OnInit } from '@angular/core';
import { User } from '../../user/user';
import { NgForm } from '@angular/forms';
import { UserService } from '../../user/user.service';
import { Router } from '@angular/router';
import { AlertService } from '../../_services';

@Component({
  selector: 'app-sign-up',
  templateUrl: './sign-up.component.html',
  styleUrls: ['./sign-up.component.css']
})
export class SignUpComponent implements OnInit {
  user: User;
  emailPattern = '^[a-z0-9.%+-]+@[a-z0-9.%-]+\.[a-z]{2,4}$';
  message: string;

  constructor(private userService: UserService,
                      private router: Router,
                      private alertService: AlertService) { }

  ngOnInit() {
    this.resetForm();
  }

  resetForm(form?: NgForm) {
    // this.message = JSON.stringify(this.user);
    if (form != null) {
    form.reset();
    }
    this.user = {
      id: null,
      email: '',
      password: '',
      fullname: '',
      username: '',
    };
  }

  OnSubmit(form: NgForm) {
    // console.log(this.user);
    // console.log(form.value);
    this.userService.create(this.user)
      .subscribe(
        data => {console.log('success: ', data);
                this.router.navigate(['/user/login']);
        },
        error => {console.log('error: ', error);
                this.alertService.error(error);
                this.resetForm(form);
        }
      );

    // .subscribe((data: any) => {
    //   if (data.Succeeded == true) {
    //     this.resetForm(form);
    //   }
  }

  // TODO: Remove this when we're done
  get diagnostic() { return JSON.stringify(this.user); }

}
