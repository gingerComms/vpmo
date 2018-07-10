import { Component, OnInit } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { AuthenticationService } from '../../_services/authentication.service';
import { Router } from '@angular/router';
import { User } from '../user';
import { UserService } from '../user.service';

@Component({
    templateUrl: './userProfile.component.html',
})

export class UserProfileComponent implements OnInit {
    userProfileForm: FormGroup;
    currentUser: User;
 

    constructor(private authService: AuthenticationService,
                private router: Router,
                private userService: UserService) { }

    ngOnInit() {
        this.authService.currentUser.subscribe(user => this.currentUser = user);
        console.log(this.currentUser.fullname + ' to be present');

        const fullname = new FormControl(this.currentUser.fullname);
        const username = new FormControl(this.currentUser.username);
        const email = new FormControl(this.currentUser.email);
        const id = new FormControl(this.currentUser.id);
        this.userProfileForm = new FormGroup({
            fullname: fullname,
            username: username,
            email: email,
            id: id,
        });
    }

    cancel() {
        this.router.navigate(['user/dashboard']);
    }

    saveProfile(formValues) {
        this.userService.update(this.currentUser.id, formValues)
            .subscribe(
                data => {
                    this.authService.updateLocalStorage(formValues.fullname, formValues.username, formValues.email);
                    console.log('success: ', data);
                    console.log(localStorage.getItem('currentUser.token'));
                    this.router.navigate(['/user/dashboard']);
                },
                err => {
                    console.log('error: ', err);
                    this.router.navigate(['user/login']);
                }
            );
    }


}
